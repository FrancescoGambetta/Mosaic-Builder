#!/usr/bin/env python3
"""
Rebuild a microscope/scan mosaic from a .spj project file and source tiles.

Default workflow:
- project directory = folder containing this script
- input directory   = <project directory>/Input
- output            = written in project directory
"""

from __future__ import annotations

import argparse
import json
import re
import statistics
import time
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

import cv2
import numpy as np


GRID_NAME_RE = re.compile(r".*_(\d{5})_(\d{5})\.[^.]+$", re.IGNORECASE)


@dataclass
class TilePose:
    basename: str
    translation_x: float
    translation_y: float
    rotation_deg: float
    scale: float
    row: Optional[int] = None
    col: Optional[int] = None
    resolved_path: Optional[Path] = None


@dataclass
class SpjSettings:
    horizontal_overlap_pct: float
    vertical_overlap_pct: float


def parse_spj(spj_path: Path) -> Tuple[SpjSettings, List[TilePose]]:
    tree = ET.parse(spj_path)
    root = tree.getroot()

    settings_node = root.find("structuredPanoramaSettings")
    if settings_node is not None:
        h_overlap = float(settings_node.attrib.get("horizontalOverlap", "10"))
        v_overlap = float(settings_node.attrib.get("verticalOverlap", "10"))
    else:
        h_overlap = 10.0
        v_overlap = 10.0

    tiles: List[TilePose] = []
    for source in root.findall("./sourceImages/sourceImage"):
        raw_path = source.attrib.get("filePath", "")
        basename = Path(raw_path.replace("\\", "/")).name
        pose = source.find("cameraPose")
        if pose is None:
            continue

        m = GRID_NAME_RE.match(basename)
        row = int(m.group(1)) if m else None
        col = int(m.group(2)) if m else None

        tiles.append(
            TilePose(
                basename=basename,
                translation_x=float(pose.attrib.get("translationX", "0")),
                translation_y=float(pose.attrib.get("translationY", "0")),
                rotation_deg=float(pose.attrib.get("rotation", "0")),
                scale=float(pose.attrib.get("scale", "1")),
                row=row,
                col=col,
            )
        )

    return SpjSettings(h_overlap, v_overlap), tiles


def resolve_tile_paths(tiles: List[TilePose], input_dir: Path) -> List[TilePose]:
    indexed = {p.name.lower(): p for p in input_dir.iterdir() if p.is_file()}

    resolved: List[TilePose] = []
    for t in tiles:
        candidate = indexed.get(t.basename.lower())
        if candidate is not None:
            t.resolved_path = candidate
            resolved.append(t)

    return resolved


def median_step_from_translations(tiles: List[TilePose], axis: str) -> Optional[float]:
    deltas: List[float] = []

    if axis == "x":
        rows = sorted({t.row for t in tiles if t.row is not None})
        for r in rows:
            row_tiles = sorted([t for t in tiles if t.row == r and t.col is not None], key=lambda t: t.col)
            for a, b in zip(row_tiles, row_tiles[1:]):
                deltas.append(abs(b.translation_x - a.translation_x))
    else:
        cols = sorted({t.col for t in tiles if t.col is not None})
        for c in cols:
            col_tiles = sorted([t for t in tiles if t.col == c and t.row is not None], key=lambda t: t.row)
            for a, b in zip(col_tiles, col_tiles[1:]):
                deltas.append(abs(b.translation_y - a.translation_y))

    deltas = [d for d in deltas if d > 1e-9]
    return statistics.median(deltas) if deltas else None


def correlation_sign(values_a: List[float], values_b: List[float]) -> int:
    if len(values_a) < 2:
        return 1
    a = np.array(values_a, dtype=np.float64)
    b = np.array(values_b, dtype=np.float64)
    if np.std(a) < 1e-12 or np.std(b) < 1e-12:
        return 1
    return 1 if np.corrcoef(a, b)[0, 1] >= 0 else -1


def build_feather_mask(h: int, w: int, feather: int) -> np.ndarray:
    if feather <= 0:
        return np.ones((h, w), dtype=np.float32)

    y = np.minimum(np.arange(h), np.arange(h)[::-1]).astype(np.float32)
    x = np.minimum(np.arange(w), np.arange(w)[::-1]).astype(np.float32)
    yy = np.clip(y / float(feather), 0.0, 1.0)
    xx = np.clip(x / float(feather), 0.0, 1.0)
    return np.outer(yy, xx).astype(np.float32)


def transform_tile(tile: np.ndarray, angle_deg: float, scale: float) -> np.ndarray:
    h, w = tile.shape[:2]
    center = (w / 2.0, h / 2.0)
    m = cv2.getRotationMatrix2D(center, angle_deg, scale)
    return cv2.warpAffine(tile, m, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REFLECT)


def rebuild_mosaic(
    tiles: List[TilePose],
    settings: SpjSettings,
    output_path: Path,
    project_dir: Path,
    input_dir: Path,
    apply_pose: bool,
    feather_px: int,
    scale_factor: float,
    max_mem_gb: float,
    log_every: int,
) -> None:
    t0 = time.time()
    print("[INFO] Starting mosaic rebuild...", flush=True)
    if not tiles:
        raise RuntimeError("No valid tiles found after path resolution.")

    first = None
    first_path = None
    for t in tiles:
        candidate = cv2.imread(str(t.resolved_path))
        if candidate is not None:
            first = candidate
            first_path = t.resolved_path
            break

    if first is None:
        raise RuntimeError(
            "No readable tile found in Input folder. "
            "Check local availability (OneDrive sync) and image integrity."
        )

    print(f"[INFO] First readable tile: {first_path}", flush=True)
    tile_h, tile_w = first.shape[:2]

    if not (0.0 < scale_factor <= 1.0):
        raise ValueError("scale_factor must be in (0, 1].")

    if scale_factor < 0.999:
        new_w = max(1, int(round(tile_w * scale_factor)))
        new_h = max(1, int(round(tile_h * scale_factor)))
        first = cv2.resize(first, (new_w, new_h), interpolation=cv2.INTER_AREA)
        tile_h, tile_w = first.shape[:2]
    print(f"[INFO] Tile size used: {tile_w}x{tile_h} (scale={scale_factor})", flush=True)

    step_px_x = tile_w * (1.0 - settings.horizontal_overlap_pct / 100.0)
    step_px_y = tile_h * (1.0 - settings.vertical_overlap_pct / 100.0)

    med_tx = median_step_from_translations(tiles, axis="x")
    med_ty = median_step_from_translations(tiles, axis="y")
    if med_tx is None or med_ty is None:
        raise RuntimeError("Unable to estimate grid steps from SPJ translations.")

    px_per_tx = step_px_x / med_tx
    px_per_ty = step_px_y / med_ty

    tiles_with_grid = [t for t in tiles if t.row is not None and t.col is not None]
    if len(tiles_with_grid) < 2:
        raise RuntimeError("Not enough tiles with parsed row/col in filename (_row_col).")

    sign_x = correlation_sign([float(t.col) for t in tiles_with_grid], [t.translation_x for t in tiles_with_grid])
    sign_y = correlation_sign([float(t.row) for t in tiles_with_grid], [t.translation_y for t in tiles_with_grid])

    tx_vals = [t.translation_x for t in tiles]
    ty_vals = [t.translation_y for t in tiles]
    tx_min, tx_max = min(tx_vals), max(tx_vals)
    ty_min, ty_max = min(ty_vals), max(ty_vals)

    placements = []
    for t in tiles:
        x = (t.translation_x - tx_min) * px_per_tx if sign_x >= 0 else (tx_max - t.translation_x) * px_per_tx
        y = (t.translation_y - ty_min) * px_per_ty if sign_y >= 0 else (ty_max - t.translation_y) * px_per_ty
        placements.append((t, int(round(x)), int(round(y))))

    min_x = min(x for _, x, _ in placements)
    min_y = min(y for _, _, y in placements)
    max_x = max(x + tile_w for _, x, _ in placements)
    max_y = max(y + tile_h for _, _, y in placements)

    canvas_w = max_x - min_x
    canvas_h = max_y - min_y
    print(f"[INFO] Canvas estimate: {canvas_w}x{canvas_h}", flush=True)

    # Rough memory estimate for acc + wgt + output buffers.
    est_bytes = canvas_h * canvas_w * (3 * 4 + 1 * 4 + 3)
    max_bytes = int(max_mem_gb * (1024 ** 3))
    if est_bytes > max_bytes:
        need = est_bytes / (1024 ** 3)
        raise MemoryError(
            f"Estimated memory {need:.1f} GB exceeds limit {max_mem_gb:.1f} GB. "
            "Use lower --scale (e.g. 0.20) or higher --max-mem-gb."
        )
    print(f"[INFO] Estimated memory: {est_bytes / (1024 ** 3):.2f} GB", flush=True)

    acc = np.zeros((canvas_h, canvas_w, 3), dtype=np.float32)
    wgt = np.zeros((canvas_h, canvas_w, 1), dtype=np.float32)
    mask = build_feather_mask(tile_h, tile_w, feather=feather_px)[:, :, None]

    normalized_placements = [(t, x - min_x, y - min_y) for (t, x, y) in placements]
    total = len(normalized_placements)
    used = 0
    for i, (t, xx, yy) in enumerate(normalized_placements, start=1):
        img = cv2.imread(str(t.resolved_path))
        if img is None:
            continue
        if apply_pose:
            img = transform_tile(img, angle_deg=t.rotation_deg, scale=t.scale)

        if scale_factor < 0.999:
            img = cv2.resize(img, (tile_w, tile_h), interpolation=cv2.INTER_AREA)

        acc[yy : yy + tile_h, xx : xx + tile_w] += img.astype(np.float32) * mask
        wgt[yy : yy + tile_h, xx : xx + tile_w] += mask
        used += 1
        if log_every > 0 and (i % log_every == 0 or i == total):
            elapsed = time.time() - t0
            print(
                f"[INFO] Blending tiles: {i}/{total} ({(100.0 * i / total):.1f}%) - elapsed {elapsed:.1f}s",
                flush=True,
            )

    if used == 0:
        raise RuntimeError("No images were accumulated on canvas.")

    out = acc / np.maximum(wgt, 1e-6)
    out = np.clip(out, 0, 255).astype(np.uint8)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"[INFO] Writing output file: {output_path}", flush=True)
    if not cv2.imwrite(str(output_path), out):
        raise RuntimeError(f"Cannot write output file: {output_path}")
    print("[INFO] Output write completed.", flush=True)

    # Always generate an annotated companion image with tile grid + labels.
    annotated = out.copy()
    line_th = max(1, int(round(min(tile_w, tile_h) / 220)))
    font = cv2.FONT_HERSHEY_SIMPLEX
    text_scale = max(0.35, min(0.9, min(tile_w, tile_h) / 700.0))
    text_th = max(1, int(round(line_th * 1.5)))

    for idx, (t, xx, yy) in enumerate(normalized_placements, start=1):
        x1, y1 = int(xx), int(yy)
        x2, y2 = int(xx + tile_w - 1), int(yy + tile_h - 1)
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (80, 255, 80), line_th, lineType=cv2.LINE_AA)

        if t.row is not None and t.col is not None:
            label = f"r{t.row} c{t.col}"
        else:
            label = f"tile {idx}"

        tx = x1 + 6
        ty = min(y2 - 6, y1 + max(18, int(24 * text_scale)))
        cv2.putText(annotated, label, (tx, ty), font, text_scale, (0, 0, 0), text_th + 2, cv2.LINE_AA)
        cv2.putText(annotated, label, (tx, ty), font, text_scale, (255, 255, 255), text_th, cv2.LINE_AA)

    annotated_path = output_path.with_name(f"{output_path.stem}_grid_labels{output_path.suffix}")
    print(f"[INFO] Writing annotated output: {annotated_path}", flush=True)
    if not cv2.imwrite(str(annotated_path), annotated):
        raise RuntimeError(f"Cannot write annotated output file: {annotated_path}")
    print("[INFO] Annotated output write completed.", flush=True)

    report = {
        "tiles_in_spj": len(tiles),
        "tiles_used": used,
        "tile_size": [tile_w, tile_h],
        "canvas_size": [canvas_w, canvas_h],
        "horizontal_overlap_pct": settings.horizontal_overlap_pct,
        "vertical_overlap_pct": settings.vertical_overlap_pct,
        "px_per_tx": px_per_tx,
        "px_per_ty": px_per_ty,
        "sign_x": sign_x,
        "sign_y": sign_y,
        "apply_pose": apply_pose,
        "feather_px": feather_px,
        "scale_factor": scale_factor,
        "project_dir": str(project_dir),
        "input_dir": str(input_dir),
        "output_file": str(output_path),
        "output_annotated_file": str(annotated_path),
    }
    report_path = output_path.with_suffix(output_path.suffix + ".json")
    report_path.write_text(json.dumps(report, indent=2), encoding="utf-8")

    print("[OK] Mosaic saved:", output_path)
    print("[OK] Annotated mosaic saved:", annotated_path)
    print("[OK] Report saved:", report_path)
    print(f"[OK] Total time: {time.time() - t0:.1f}s", flush=True)


def find_spj_in_folder(input_dir: Path, spj_name: Optional[str]) -> Path:
    if spj_name:
        spj = input_dir / spj_name
        if not spj.exists():
            raise FileNotFoundError(f"SPJ not found in input folder: {spj}")
        return spj

    spjs = sorted(input_dir.glob("*.spj"))
    if len(spjs) == 1:
        return spjs[0]
    if len(spjs) == 0:
        raise FileNotFoundError(f"No .spj found in input folder: {input_dir}")
    raise RuntimeError("Multiple .spj found in Input. Use --spj-name to choose one.")


def main() -> None:
    script_dir = Path(__file__).resolve().parent

    parser = argparse.ArgumentParser(
        description="Rebuild a grid mosaic from .spj camera poses. Defaults: ./Input -> output in script folder."
    )
    parser.add_argument(
        "--project-dir",
        default=str(script_dir),
        help="Project folder (default: folder containing this script)",
    )
    parser.add_argument(
        "--input-dir",
        help="Input folder with .spj + tiles (default: <project-dir>/Input)",
    )
    parser.add_argument("--spj-name", help="Optional SPJ filename inside input-dir (e.g. BAR1.spj)")
    parser.add_argument(
        "--output-name",
        help="Output filename only. Saved in project-dir. Default: <spj_stem>_grid_mosaic.png",
    )
    parser.add_argument("--apply-pose", action="store_true", help="Apply per-tile rotation/scale from cameraPose")
    parser.add_argument("--feather", type=int, default=48, help="Feather radius in pixels (default: 48)")
    parser.add_argument(
        "--scale",
        type=float,
        default=0.25,
        help="Global downscale factor in (0,1]. Default 0.25 to avoid memory crashes.",
    )
    parser.add_argument(
        "--max-mem-gb",
        type=float,
        default=10.0,
        help="Safety memory limit for internal buffers. Default 10 GB.",
    )
    parser.add_argument(
        "--log-every",
        type=int,
        default=25,
        help="Progress log frequency in tiles. Default 25.",
    )

    args = parser.parse_args()

    project_dir = Path(args.project_dir).resolve()
    if not project_dir.exists():
        raise FileNotFoundError(
            f"Project folder not found: {project_dir}\n"
            "Tip: run this script from its own folder or pass --project-dir explicitly."
        )

    input_dir = Path(args.input_dir).resolve() if args.input_dir else (project_dir / "Input")
    if not input_dir.exists():
        raise FileNotFoundError(
            f"Input folder not found: {input_dir}\n"
            f"Expected structure:\n"
            f"  {project_dir}\\Input\\<project>.spj\n"
            f"  {project_dir}\\Input\\<tiles>.JPG"
        )

    spj_path = find_spj_in_folder(input_dir, args.spj_name)

    output_name = args.output_name if args.output_name else f"{spj_path.stem}_grid_mosaic.png"
    output_path = project_dir / Path(output_name).name

    settings, tiles = parse_spj(spj_path)
    tiles = resolve_tile_paths(tiles, input_dir=input_dir)

    if len(tiles) < 2:
        raise RuntimeError("Not enough tiles resolved in input folder.")

    rebuild_mosaic(
        tiles=tiles,
        settings=settings,
        output_path=output_path,
        project_dir=project_dir,
        input_dir=input_dir,
        apply_pose=args.apply_pose,
        feather_px=max(0, int(args.feather)),
        scale_factor=float(args.scale),
        max_mem_gb=float(args.max_mem_gb),
        log_every=max(0, int(args.log_every)),
    )


if __name__ == "__main__":
    main()

