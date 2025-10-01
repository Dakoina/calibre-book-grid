# Calibre Book Grid

A Python-based tool to export and visualize your Calibre library as an interactive web interface. The tool extracts book metadata from your Calibre database, processes cover images, and generates a beautiful grid-based web viewer.

![Project Banner](https://img.shields.io/badge/Python-3.8+-blue.svg)
![License](https://img.shields.io/badge/license-MIT-green.svg)

## 📋 Table of Contents

- [Features](#features)
- [Screenshots](#screenshots)
- [Requirements](#requirements)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Command Line Options](#command-line-options)
- [Output Files](#output-files)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)

## ✨ Features

### Data Export
- **Metadata Extraction**: Extract all book information from Calibre's SQLite database
- **Cover Processing**: Automatically resize and convert covers to WebP format
- **Multiple Export Formats**: JSON, CSV, and optimized image files
- **Language Detection**: Extract and export all languages in your library
- **Smart Caching**: Hash-based system to avoid reprocessing unchanged covers
- **Read Status**: Track which books you've read

## 🖼️ Screenshots

*(Add screenshots of your web interface here)*

## 📦 Requirements

- **Python 3.8+**
- **Calibre** library with `metadata.db`
- Python packages (see `requirements.txt`):
  - Pillow >= 9.0
  - numpy >= 1.24
  - tqdm >= 4.0

## 🚀 Installation

### 1. Clone the Repository

    git clone [https://github.com/yourusername/CalibreBookGrid.git](https://github.com/yourusername/CalibreBookGrid.git) cd CalibreBookGrid

### 2. Create Virtual Environment (Recommended)

#### Windows
    python -m venv .venv .venv\Scripts\activate
#### macOS/Linux
    python3 -m venv .venv source .venv/bin/activate


### 3. Install Dependencies
    bash pip install -r requirements.txt

## ⚙️ Configuration

Edit the configuration section in `main.py`:

    CALIBRE_LIBRARY_PATH = "C:\Users\YourName\Calibre Library"
    DB_PATH = os.path.join(CALIBRE_LIBRARY_PATH, "metadata.db") 
    JSON_OUTPUT_PATH = "books.json" 
    CSV_OUTPUT_PATH = "calibre_books_export.csv" 
    LANGUAGES_OUTPUT_PATH = "languages.json" 
    OUTPUT_COVER_FOLDER = "covers" 
    MAX_COVER_WIDTH = 400 
    COVER_QUALITY = 80

**Important**: 
Update `CALIBRE_LIBRARY_PATH` to point to your Calibre library location.

## 🎯 Usage

### Basic Usage

    python main.py

This will:
1. ✅ Validate your Calibre library
2. 📚 Extract all book metadata
3. 🌍 Extract available languages
4. 💾 Export to JSON and CSV
5. 🖼️ Process and resize all cover images to WebP
6. 🎨 Calculate average cover colors

### Advanced Usage

    python main.py --help

### Common Commands

| Command | Description | Example |
| --- | --- | --- |
| `-v`, `--verbose` | Enable detailed output | `python main.py -v` |
| `--skip-covers` | Only export data, skip cover processing | `python main.py --skip-covers` |
| `--skip-csv` | Skip CSV export | `python main.py --skip-csv` |
| `--quality N` | Set WebP quality (1-100, default: 80) | `python main.py --quality 90` |
| `--max-width N` | Set max cover width in pixels (default: 400) | `python main.py --max-width 600` |
| `--force-reprocess` | Reprocess all covers (ignore cache) | `python main.py --force-reprocess` |
| `--library-path PATH` | Use different Calibre library | `python main.py --library-path "D:\Books"` |

### Example commands

#### Verbose output with high quality
`python main.py -v --quality 95`
#### Quick data export (no cover processing)
`python main.py --skip-covers`
#### Force rebuild all covers at larger size
`python main.py --force-reprocess --max-width 600 --quality 90`
#### Use different library location
`python main.py --library-path "D:\My Calibre Library" -v`

## 📄 Output Files
After running the script, the following files will be generated:

| File | Description |
| --- | --- |
| `books.json` | Complete book metadata with processed cover paths and colors |
| `calibre_books_export.csv` | CSV export of all book data |
| `languages.json` | Array of distinct language codes found in your library |
| `covers/*.webp` | Resized and optimized cover images |


### JSON Structure

**books.json**

```json
[
    {
    "id": 1,
    "author": "Author Name",
    "title": "Book Title",
    "series": "Series Name",
    "series_index": 1.0,
    "cover_path": "covers/1.webp",
    "cover_hash": "sha256...",
    "cover_color": [123, 145, 167],
    "is_read": 0
    }
]
```
**languages.json**

```json
["deu", "eng", "fra", "nld", "spa"]
```

## 🐛 Troubleshooting
### "Calibre library was not found"
- Check that points to the correct directory `CALIBRE_LIBRARY_PATH`
- Ensure `metadata.db` exists in that directory
- Use `--library-path` to specify a different location

### Covers Not Processing

Try verbose mode to see detailed errors

    python main.py -v

Force reprocess all covers

    python main.py --force-reprocess


### Memory Issues with Large Libraries

Process covers only, skip CSV

    python main.py --skip-csv

Use lower quality to save space
    
    python main.py --quality 70

Smaller cover size

    python main.py --max-width 300

### Pillow/Image Errors

#### Reinstall Pillow

    pip uninstall Pillow
    pip install Pillow --upgrade


**Made with ❤️ for book lovers**
