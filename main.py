import sqlite3
import json
import os
import csv
import sys
import argparse
from tqdm import tqdm
from PIL import Image
import hashlib


# === CONFIGURATION ===
CALIBRE_LIBRARY_PATH = "C:\\Users\\debon\\Calibre Bibliotheek"
DB_PATH = os.path.join(CALIBRE_LIBRARY_PATH, "metadata.db")
JSON_OUTPUT_PATH = "books.json"
CSV_OUTPUT_PATH = "calibre_books_export.csv"
LANGUAGES_OUTPUT_PATH = "languages.json"
OUTPUT_COVER_FOLDER = "covers"
MAX_COVER_WIDTH = 400
COVER_QUALITY = 80

# Global verbose flag
VERBOSE = False


# === ARGUMENT PARSER ===

def parse_arguments():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Export and process Calibre library books and covers",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python main.py                          # Run normally
  python main.py --verbose                # Show detailed output
  python main.py --skip-covers            # Don't process covers
  python main.py --quality 90             # Use higher quality for covers
  python main.py --max-width 600          # Larger cover size
  python main.py -v --skip-csv            # Combine multiple options
        """
    )

    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Enable verbose output with detailed information'
    )

    parser.add_argument(
        '--skip-covers',
        action='store_true',
        help='Skip cover processing (only export data)'
    )

    parser.add_argument(
        '--skip-csv',
        action='store_true',
        help='Skip CSV export'
    )

    parser.add_argument(
        '--quality',
        type=int,
        default=COVER_QUALITY,
        metavar='N',
        help=f'JPEG/WebP quality (1-100, default: {COVER_QUALITY})'
    )

    parser.add_argument(
        '--max-width',
        type=int,
        default=MAX_COVER_WIDTH,
        metavar='N',
        help=f'Maximum cover width in pixels (default: {MAX_COVER_WIDTH})'
    )

    parser.add_argument(
        '--library-path',
        type=str,
        default=CALIBRE_LIBRARY_PATH,
        metavar='PATH',
        help='Path to Calibre library (default: configured path)'
    )

    parser.add_argument(
        '--force-reprocess',
        action='store_true',
        help='Force reprocessing of all covers (ignore hash cache)'
    )

    return parser.parse_args()


# === UTILITY FUNCTIONS ===

def log_verbose(message):
    """Print message only if verbose mode is enabled."""
    if VERBOSE:
        print(f"  [VERBOSE] {message}")


def sha256_of_file(path: str, chunk_size: int = 8192) -> str:
    """Calculate SHA256 hash of a file."""
    log_verbose(f"Calculating hash for: {path}")
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    hash_value = h.hexdigest()
    log_verbose(f"Hash: {hash_value}")
    return hash_value


def validate_calibre_library(library_path):
    """Validate that the Calibre library exists."""
    db_path = os.path.join(library_path, "metadata.db")
    if not os.path.isfile(db_path):
        print(f"❌ Calibre library was not found: metadata.db is missing at {library_path}")
        sys.exit(1)
    print(f"✅ Calibre library found at: {library_path}")
    log_verbose(f"Database path: {db_path}")
    return db_path


def setup_output_folders():
    """Create necessary output folders."""
    os.makedirs(OUTPUT_COVER_FOLDER, exist_ok=True)
    print(f"✅ Output folder ready: {OUTPUT_COVER_FOLDER}")


# === DATABASE FUNCTIONS ===

def fetch_books_from_db(db_path):
    """Fetch all books from Calibre database."""
    log_verbose(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    log_verbose("Executing query to fetch books...")
    cursor.execute("""
                   SELECT books.id,
                          books.title,
                          group_concat(authors.name, ', ') AS authors,
                          series.name                      AS series,
                          books.series_index,
                          books.path                       AS book_folder,
                          COALESCE(custom_column_1.value, 0) AS is_read
                   FROM books
                            LEFT JOIN books_authors_link ON books.id = books_authors_link.book
                            LEFT JOIN authors ON books_authors_link.author = authors.id
                            LEFT JOIN books_series_link ON books.id = books_series_link.book
                            LEFT JOIN series ON books_series_link.series = series.id
                            LEFT JOIN custom_column_1 ON books.id = custom_column_1.book
                   GROUP BY books.id
                   ORDER BY authors, series, books.title
                   """)

    books = []
    for row in cursor.fetchall():
        book_id = row[0]
        title = row[1]
        authors = row[2]
        series = row[3] if row[3] else ''
        series_index = row[4] if row[4] is not None else ''
        book_folder = row[5]
        is_read = row[6]

        # Full path to cover
        library_path = os.path.dirname(db_path)
        cover_path = os.path.join(library_path, book_folder, "cover.jpg")
        if not os.path.exists(cover_path):
            cover_path = ""
            log_verbose(f"Cover not found for book {book_id}: {title}")

        books.append({
            "id": book_id,
            "author": authors,
            "title": title,
            "series": series,
            "series_index": series_index,
            "cover_path": cover_path,
            "is_read": is_read
        })

    conn.close()
    print(f"✅ Fetched {len(books)} books from database")
    return books


def fetch_languages_from_db(db_path):
    """Fetch distinct languages from Calibre database."""
    log_verbose(f"Connecting to database: {db_path}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    log_verbose("Executing query to fetch languages...")
    cursor.execute("""
                   SELECT DISTINCT languages.lang_code
                   FROM languages
                   ORDER BY languages.lang_code
                   """)

    languages = [row[0] for row in cursor.fetchall() if row[0]]
    conn.close()

    print(f"✅ Found {len(languages)} distinct languages")
    log_verbose(f"Languages: {languages}")
    return languages


# === EXPORT FUNCTIONS ===

def print_books_to_terminal(books):
    """Print books to terminal for debugging."""
    if not VERBOSE:
        return

    print("\n📚 Books in library:")
    for book in books:
        print(f"{book['id']} | {book['author']} | {book['title']} | "
              f"{book['series']} | {book['series_index']} | {book['cover_path']}")


def export_to_csv(books):
    """Export books to CSV file."""
    if not books:
        print("⚠️  No books to export to CSV")
        return

    log_verbose(f"Writing {len(books)} books to CSV...")
    with open(CSV_OUTPUT_PATH, mode="w", newline='', encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=books[0].keys())
        writer.writeheader()
        writer.writerows(books)

    print(f"✅ Exported to {CSV_OUTPUT_PATH}")


def save_books_to_json(books):
    """Save books data to JSON file."""
    log_verbose(f"Writing {len(books)} books to JSON...")
    with open(JSON_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)

    print(f"✅ Exported to {JSON_OUTPUT_PATH}")


def save_languages_to_json(languages):
    """Save languages to JSON file."""
    log_verbose(f"Writing {len(languages)} languages to JSON...")
    with open(LANGUAGES_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(languages, f, ensure_ascii=False, indent=2)

    print(f"✅ Exported {len(languages)} languages to {LANGUAGES_OUTPUT_PATH}")
    if languages:
        print(f"   Languages found: {', '.join(languages)}")


def load_books_from_json():
    """Load books from JSON file."""
    log_verbose(f"Reading books from {JSON_OUTPUT_PATH}...")
    with open(JSON_OUTPUT_PATH, "r", encoding="utf-8") as f:
        books = json.load(f)

    print(f"✅ Loaded {len(books)} books from {JSON_OUTPUT_PATH}")
    return books


# === COVER PROCESSING FUNCTIONS ===

def calculate_average_color(img):
    """Calculate average color of an image."""
    avg_color = img.resize((1, 1)).getpixel((0, 0))
    log_verbose(f"Average color: RGB{avg_color}")
    return avg_color


def process_single_cover(book, original_cover, book_id, quality, max_width, force_reprocess=False):
    """Process a single book cover: resize and convert."""
    new_cover_path = os.path.join(OUTPUT_COVER_FOLDER, f"{book_id}.webp")

    log_verbose(f"Processing cover for book {book_id}: {book.get('title', 'Unknown')}")

    # Calculate hash of source file
    current_hash = None
    if original_cover and os.path.exists(original_cover):
        try:
            current_hash = sha256_of_file(original_cover)
        except Exception as e:
            print(f"❌ Error hashing cover for book ID {book_id}: {e}")
            return None, "failed"

    # Skip if already processed and unchanged
    previous_hash = book.get("cover_hash")
    if not force_reprocess and os.path.exists(new_cover_path) and current_hash and previous_hash == current_hash:
        book["cover_path"] = f"covers/{book_id}.webp"
        log_verbose(f"Skipping book {book_id}: hash unchanged")
        return None, "skipped"

    # Process the cover
    if not original_cover or not os.path.exists(original_cover):
        book["cover_path"] = ""
        log_verbose(f"Missing cover for book {book_id}")
        return None, "missing"

    try:
        with Image.open(original_cover) as img:
            original_size = img.size
            log_verbose(f"Original image size: {original_size}")

            img = img.convert("RGB")

            # Resize if needed
            if img.width > max_width:
                ratio = max_width / img.width
                new_size = (max_width, int(img.height * ratio))
                img = img.resize(new_size, Image.LANCZOS)
                log_verbose(f"Resized to: {new_size}")
            else:
                log_verbose("No resize needed")

            # Save as WebP
            img.save(new_cover_path, "WEBP", quality=quality)
            file_size = os.path.getsize(new_cover_path)
            log_verbose(f"Saved as WebP: {file_size} bytes (quality={quality})")

            # Update book data
            book["cover_path"] = f"covers/{book_id}.webp"
            if current_hash:
                book["cover_hash"] = current_hash

            # Calculate average color
            avg_color = calculate_average_color(img)
            book["cover_color"] = avg_color

            return book, "success"

    except Exception as e:
        print(f"❌ Error processing book ID {book_id}: {e}")
        book["cover_path"] = ""
        return book, "failed"


def process_all_covers(books, quality, max_width, force_reprocess=False):
    """Process all book covers: resize, convert to WebP, and calculate colors."""
    copied = 0
    skipped = 0
    failed = 0

    print(f"\n📦 Processing {len(books)} covers (max width {max_width}px, quality {quality})...")
    if force_reprocess:
        print("   Force reprocess enabled - ignoring cache")

    for book in tqdm(books, desc="Processing covers", unit="book", disable=VERBOSE):
        original_cover = book["cover_path"]
        book_id = book["id"]

        result, status = process_single_cover(book, original_cover, book_id, quality, max_width, force_reprocess)

        if status == "success":
            copied += 1
        elif status == "skipped":
            skipped += 1
        elif status in ["failed", "missing"]:
            failed += 1

    # Print summary
    print("\n✅ Cover processing summary:")
    print(f"   Processed: {copied}")
    print(f"   Skipped (unchanged): {skipped}")
    print(f"   Failed/missing: {failed}")

    return books


# === MAIN EXECUTION ===

def main():
    """Main execution function."""
    global VERBOSE

    # Parse command line arguments
    args = parse_arguments()
    VERBOSE = args.verbose

    print("🚀 Starting Calibre library export...\n")

    if VERBOSE:
        print("=" * 60)
        print("VERBOSE MODE ENABLED")
        print("=" * 60)
        print(f"Settings:")
        print(f"  Library path: {args.library_path}")
        print(f"  Skip covers: {args.skip_covers}")
        print(f"  Skip CSV: {args.skip_csv}")
        print(f"  Cover quality: {args.quality}")
        print(f"  Max width: {args.max_width}")
        print(f"  Force reprocess: {args.force_reprocess}")
        print("=" * 60)
        print()

    # Setup
    db_path = validate_calibre_library(args.library_path)
    setup_output_folders()

    # Fetch data from database
    books = fetch_books_from_db(db_path)
    languages = fetch_languages_from_db(db_path)

    # Export initial data
    print_books_to_terminal(books)

    if not args.skip_csv:
        export_to_csv(books)
    else:
        print("⏭️  Skipping CSV export")

    save_books_to_json(books)
    save_languages_to_json(languages)

    # Process covers
    if not args.skip_covers:
        books = load_books_from_json()
        books = process_all_covers(books, args.quality, args.max_width, args.force_reprocess)
        save_books_to_json(books)
    else:
        print("⏭️  Skipping cover processing")

    print(f"\n🎉 Export complete! Data saved to {JSON_OUTPUT_PATH}")


if __name__ == "__main__":
    main()