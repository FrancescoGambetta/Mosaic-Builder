from pathlib import Path
import cv2
import numpy as np
from PIL import Image
from PIL.ExifTags import TAGS
from datetime import datetime


# ============================================================
# AUTOMATIC STITCHING OF N IMAGES INTO A SINGLE MOSAIC
# ============================================================
# Usage:
#   python Mosaic_builder.py
#
# AUTOMATIC ORDERING:
#   - Priority 1: EXIF timestamp (photo capture date/time)
#   - Fallback: Alphabetical filename
#   No need to rename photos as 01.jpg, 02.jpg, etc. anymore!
#
# Only modify these variables:
INPUT_DIR = r"./input_images"
OUTPUT_FILE = r"./mosaic_result.png"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}
TRY_SCANS_MODE = False   # False = classic panorama, True = scans for more planar images
# ============================================================


def get_exif_timestamp(image_path: Path):
    """
    Extracts EXIF timestamp from photo.
    Returns None if not available.
    """
    try:
        img = Image.open(image_path)
        exif_data = img._getexif()
        
        if exif_data:
            # Look for common tags for capture date
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, tag_id)
                if tag_name in ['DateTimeOriginal', 'DateTime', 'DateTimeDigitized']:
                    # Typical format: '2024:01:15 14:30:45'
                    return datetime.strptime(value, '%Y:%m:%d %H:%M:%S')
        return None
    except Exception:
        return None


def load_images_from_folder(folder: str):
    folder_path = Path(folder)
    if not folder_path.exists():
        raise FileNotFoundError(f"Folder not found: {folder}")

    # Collect all image paths
    image_paths = [
        p for p in folder_path.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS
    ]

    if len(image_paths) < 2:
        raise ValueError("At least 2 images are required.")

    # Intelligent sorting: EXIF timestamp → filename
    print("[INFO] Ordering images...")
    paths_with_time = []
    exif_count = 0
    
    for p in image_paths:
        timestamp = get_exif_timestamp(p)
        if timestamp:
            exif_count += 1
            paths_with_time.append((timestamp, p.name, p))
        else:
            # Use minimum epoch to put at the end, then sort by name
            paths_with_time.append((datetime.min, p.name, p))
    
    # Sort by (timestamp, name)
    paths_with_time.sort(key=lambda x: (x[0], x[1]))
    image_paths = [p[2] for p in paths_with_time]
    
    print(f"[INFO] {exif_count}/{len(image_paths)} images with EXIF timestamp")
    if exif_count < len(image_paths):
        print(f"[INFO] {len(image_paths) - exif_count} images sorted by filename")

    images = []
    valid_paths = []

    for p in image_paths:
        img = cv2.imread(str(p))
        if img is None:
            print(f"[WARN] Unable to read: {p}")
            continue
        images.append(img)
        valid_paths.append(p)

    if len(images) < 2:
        raise ValueError("Not enough valid images to merge.")

    print("Images loaded (in order):")
    for p in valid_paths:
        print(f" - {p.name}")

    return images, valid_paths


def crop_black_borders(image: np.ndarray) -> np.ndarray:
    """
    Crops black borders from the final mosaic.
    """
    if image is None or image.size == 0:
        return image

    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    _, thresh = cv2.threshold(gray, 1, 255, cv2.THRESH_BINARY)

    contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    if not contours:
        return image

    largest = max(contours, key=cv2.contourArea)
    x, y, w, h = cv2.boundingRect(largest)
    cropped = image[y:y + h, x:x + w]

    return cropped


def stitch_images(images, scans_mode=False):
    """
    Uses OpenCV stitcher.
    """
    mode = cv2.Stitcher_SCANS if scans_mode else cv2.Stitcher_PANORAMA
    stitcher = cv2.Stitcher_create(mode)

    # Confidence parameters. Ignored if your OpenCV build doesn't support them.
    try:
        stitcher.setPanoConfidenceThresh(0.6)
    except Exception:
        pass

    status, stitched = stitcher.stitch(images)
    return status, stitched


def resize_if_too_large(images, max_width=2200):
    """
    Temporarily reduces very large images to improve stitching
    probability and reduce RAM/time.
    """
    resized = []
    for img in images:
        h, w = img.shape[:2]
        if w > max_width:
            scale = max_width / w
            new_size = (int(w * scale), int(h * scale))
            img = cv2.resize(img, new_size, interpolation=cv2.INTER_AREA)
        resized.append(img)
    return resized


def main():
    print("[INFO] Loading images...")
    images, paths = load_images_from_folder(INPUT_DIR)

    print("[INFO] Attempting stitching on original images...")
    status, stitched = stitch_images(images, scans_mode=TRY_SCANS_MODE)

    if status != cv2.Stitcher_OK:
        print(f"[WARN] Stitching failed with status={status}.")
        print("[INFO] Retrying on reduced versions...")
        small_images = resize_if_too_large(images)
        status, stitched = stitch_images(small_images, scans_mode=TRY_SCANS_MODE)

    if status != cv2.Stitcher_OK or stitched is None:
        print("\n" + "="*70)
        print("❌ STITCHING FAILED")
        print("="*70)
        print(f"OpenCV status code: {status}")
        print("\n💡 SUGGESTIONS:")
        print("   1. Verify there is sufficient overlap between images")
        print("   2. Check that images are in the correct order")
        print("   3. TRY RENAMING FILES manually in sequential order:")
        print("      Example: 01.jpg, 02.jpg, 03.jpg, 04.jpg, ...")
        print("      This forces the order you want, ignoring EXIF")
        print("   4. If using very different images, try TRY_SCANS_MODE = True")
        print("="*70 + "\n")
        raise RuntimeError("Stitching failed.")

    print("[INFO] Cropping black borders...")
    stitched = crop_black_borders(stitched)

    output_path = Path(OUTPUT_FILE)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    ok = cv2.imwrite(str(output_path), stitched)
    if not ok:
        raise RuntimeError(f"Unable to save file: {OUTPUT_FILE}")

    print("\n" + "="*70)
    print(f"✅ MOSAIC SAVED SUCCESSFULLY!")
    print("="*70)
    print(f"📁 Path: {output_path.resolve()}")
    print(f"📐 Dimensions: {stitched.shape[1]} x {stitched.shape[0]} px")
    print("\n💡 NOTE:")
    print("   If the mosaic is not to your liking or the order is wrong,")
    print("   try RENAMING FILES in the input folder in numerical order:")
    print("   Example: 01_left.jpg, 02_center.jpg, 03_right.jpg, ...")
    print("   Manual ordering overrides automatic EXIF ordering.")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
