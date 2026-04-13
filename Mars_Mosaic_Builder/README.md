# 🖼️ Mosaic Builder

Automatic image stitching tool that creates panoramic mosaics from multiple photos using OpenCV. No need to manually rename your photos - the tool intelligently orders them based on EXIF timestamps!

## ✨ Features

- 🤖 **Automatic Ordering**: Uses EXIF timestamp data to order photos chronologically
- 📁 **Fallback Support**: Falls back to alphabetical filename ordering if EXIF is unavailable
- 🔄 **Smart Retry**: Automatically resizes images and retries if stitching fails
- ✂️ **Auto Crop**: Removes black borders from the final mosaic
- 🎯 **Two Modes**: Classic panorama mode or scans mode for planar images
- 💡 **Helpful Suggestions**: Clear error messages with actionable recommendations

## 📋 Requirements

- Python 3.7+
- OpenCV
- Pillow (PIL)
- NumPy

## 🚀 Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mosaic-builder.git
cd mosaic-builder
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## 📖 Usage

1. Place your images in the `./input_images` folder (or modify `INPUT_DIR` in the script)

2. Run the script:
```bash
python Mosaic_builder.py
```

3. Find your mosaic in `./mosaic_result.png` (or your custom `OUTPUT_FILE`)

### Configuration

Edit these variables at the top of `Mosaic_builder.py`:

```python
INPUT_DIR = r"./input_images"          # Folder containing your images
OUTPUT_FILE = r"./mosaic_result.png"   # Output filename
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp"}
TRY_SCANS_MODE = False                 # False = panorama, True = scans
```

## 🎯 How It Works

### Automatic Ordering

The tool uses a two-tier ordering system:

1. **EXIF Timestamp** (Priority 1): Reads the photo capture date/time from EXIF metadata
2. **Filename** (Fallback): If EXIF is not available, sorts alphabetically by filename

This means you can shoot a panorama with your camera, and the photos will be automatically stitched in the correct order - no renaming required!

### Stitching Process

1. Loads all images from the input folder
2. Orders them intelligently (EXIF → filename)
3. Attempts stitching with OpenCV's panorama stitcher
4. If it fails, resizes images and retries
5. Crops black borders from the result
6. Saves the final mosaic

## 💡 Troubleshooting

### If stitching fails:

The script will show helpful suggestions:

```
❌ STITCHING FAILED
======================================================================
💡 SUGGESTIONS:
   1. Verify there is sufficient overlap between images
   2. Check that images are in the correct order
   3. TRY RENAMING FILES manually in sequential order:
      Example: 01.jpg, 02.jpg, 03.jpg, 04.jpg, ...
      This forces the order you want, ignoring EXIF
   4. If using very different images, try TRY_SCANS_MODE = True
```

### Common Issues

- **Not enough overlap**: Make sure your photos overlap by at least 30-40%
- **Wrong order**: Try manually renaming files as `01.jpg, 02.jpg, 03.jpg, ...`
- **Different lighting**: Shoot in consistent lighting conditions
- **Moving objects**: Avoid people/cars moving between shots

## 📂 Project Structure

```
mosaic-builder/
├── Mosaic_builder.py      # Main script
├── requirements.txt       # Python dependencies
├── README.md             # This file
├── input_images/         # Place your images here
│   ├── photo1.jpg
│   ├── photo2.jpg
│   └── photo3.jpg
└── mosaic_result.png     # Output will be saved here
```

## 🖼️ Example

### Input
```
input_images/
├── DSC_001.jpg
├── DSC_002.jpg
├── DSC_003.jpg
└── DSC_004.jpg
```

### Output
A single panoramic image: `mosaic_result.png`

### Console Output
```
[INFO] Loading images...
[INFO] Ordering images...
[INFO] 4/4 images with EXIF timestamp
Images loaded (in order):
 - DSC_001.jpg
 - DSC_002.jpg
 - DSC_003.jpg
 - DSC_004.jpg
[INFO] Attempting stitching on original images...
[INFO] Cropping black borders...

======================================================================
✅ MOSAIC SAVED SUCCESSFULLY!
======================================================================
📁 Path: /path/to/mosaic_result.png
📐 Dimensions: 4200 x 1800 px
```

## 🤝 Contributing

Contributions are welcome! Feel free to:

- Report bugs
- Suggest new features
- Submit pull requests

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- Built with [OpenCV](https://opencv.org/)
- EXIF reading powered by [Pillow](https://python-pillow.org/)

## 📧 Contact

If you have questions or suggestions, feel free to open an issue!

---
