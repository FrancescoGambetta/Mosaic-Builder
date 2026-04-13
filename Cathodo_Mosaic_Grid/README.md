# Grid Rebuild from SPJ

Ricostruzione di mosaici da acquisizioni a griglia usando metadati `.spj`.

## Quick Start
Il comportamento predefinito (senza parametri) e:
- cartella progetto = cartella dove si trova `rebuild_from_spj.py`
- input = `./Input` dentro la cartella progetto
- output = sempre nella cartella progetto

Struttura attesa:
```text
grid_rebuild_spj/
  rebuild_from_spj.py
  Input/
    BAR1.spj
    BAR1_00000_00000.JPG
    BAR1_00000_00001.JPG
    ...
```

Esecuzione base:
```powershell
python .\rebuild_from_spj.py
```

## Output Generati
- `NOME_grid_mosaic.png`: mosaico base.
- `NOME_grid_mosaic_grid_labels.png`: mosaico annotato con griglia + label tile (es. `r3 c16`, senza zeri iniziali).
- `NOME_grid_mosaic.png.json`: report tecnico (dimensioni, scala, overlap, parametri stimati).

## Opzioni Principali
- `--spj-name BAR1.spj`: usa uno specifico `.spj` se in `Input` ce ne sono piu di uno.
- `--output-name risultato.png`: nome output (salvato in cartella progetto).
- `--apply-pose`: applica `rotation`/`scale` da `cameraPose`.
- `--feather 64`: regola il blending nelle aree di overlap.
- `--scale 0.25`: downscale globale (default consigliato per stabilita RAM).
- `--max-mem-gb 10`: limite memoria di sicurezza.
- `--log-every 10`: frequenza log progresso (in numero di tile).

## Esempi Utili
Esecuzione piu rapida e stabile:
```powershell
python .\rebuild_from_spj.py --scale 0.20 --log-every 10
```

Esecuzione con posa geometrica:
```powershell
python .\rebuild_from_spj.py --apply-pose --scale 0.25 --log-every 10
```

Input o progetto personalizzati:
```powershell
python .\rebuild_from_spj.py --project-dir "C:\path\project" --input-dir "C:\path\project\Input"
```

## Troubleshooting Rapido
- `Input folder not found`: crea la cartella `Input` nella cartella progetto, oppure passa `--input-dir`.
- `No .spj found in input folder`: metti un file `.spj` in `Input`.
- `Multiple .spj found in Input`: passa `--spj-name`.
- `Estimated memory ... exceeds limit`: riduci `--scale` (es. `0.20`) o aumenta `--max-mem-gb`.
- Blocco percepito in terminale: usa `--log-every 10` per vedere progresso piu frequente.
