import sqlite3
import json
import os
import csv
import shutil
from tqdm import tqdm
from PIL import Image
import hashlib
import sys  # place alongside your other imports

# === CONFIGURATION ===
calibre_library_path = "C:\\Users\\debon\\Calibre Bibliotheek"
db_path = os.path.join(calibre_library_path, "metadata.db")
json_output_path = "books.json"
output_cover_folder = "covers"
output_json_path = json_output_path

# === VALIDATE CALIBRE METADATA DB PATH ===
if not os.path.isfile(db_path):
    print("Calibre library was not found: metadata.db is missing at the configured path.")
    sys.exit(1)

# === CREATE COVER FOLDER ===
os.makedirs(output_cover_folder, exist_ok=True)

def sha256_of_file(path: str, chunk_size: int = 8192) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(chunk_size), b""):
            h.update(chunk)
    return h.hexdigest()

# === CONNECT TO DB ===
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# === RUN QUERY ===
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

# === PROCESS RESULTS ===
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
    cover_path = os.path.join(calibre_library_path, book_folder, "cover.jpg")
    if not os.path.exists(cover_path):
        cover_path = ""

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

# === PRINT TO TERMINAL ===
for book in books:
    print(
        f"{book['id']} | {book['author']} | {book['title']} | {book['series']} | {book['series_index']} | {book['cover_path']}")

# === OPTIONAL: EXPORT TO CSV ===
output_path = "calibre_books_export.csv"
with open(output_path, mode="w", newline='', encoding="utf-8") as file:
    writer = csv.DictWriter(file, fieldnames=books[0].keys())
    writer.writeheader()
    writer.writerows(books)

print(f"\n✅ Exported to {output_path}")

# === export to JSON ===
with open(json_output_path, "w", encoding="utf-8") as f:
    json.dump(books, f, ensure_ascii=False, indent=2)

print(f"✅ Exported to {json_output_path}")

# === LOAD BOOKS JSON ===
with open(output_json_path, "r", encoding="utf-8") as f:
    books = json.load(f)

# === UPDATE COVER PATHS AND COPY/RESIZE FILES ===
copied = 0
skipped = 0
failed = 0

print(f"\n📦 Processing {len(books)} covers (max width 400px)...")

for book in tqdm(books, desc="Updating/resizing covers", unit="book"):
    original_cover = book["cover_path"]
    book_id = book["id"]
    new_cover_path = os.path.join(output_cover_folder, f"{book_id}.jpg")

    # Determine current source hash (if source exists)
    current_hash = None
    if original_cover and os.path.exists(original_cover):
        try:
            current_hash = sha256_of_file(original_cover)
        except Exception as e:
            print(f"❌ Error hashing cover for book ID {book_id}: {e}")
            current_hash = None

    # Decide whether to skip based on hash match and presence of resized file
    previous_hash = book.get("cover_hash")
    if os.path.exists(new_cover_path) and current_hash and previous_hash == current_hash:
        book["cover_path"] = f"covers/{book_id}.jpg"
        skipped += 1
        continue

    if original_cover and os.path.exists(original_cover):
        try:
            with Image.open(original_cover) as img:
                img = img.convert("RGB")
                if img.width > 400:
                    ratio = 400 / img.width
                    new_size = (400, int(img.height * ratio))
                    img = img.resize(new_size, Image.LANCZOS)
                img.save(new_cover_path, "JPEG", quality=85)
                book["cover_path"] = f"covers/{book_id}.jpg"
                if current_hash:
                    book["cover_hash"] = current_hash
                copied += 1

                # Calculate average color (simple pixel mean)
                avg_color = img.resize((1, 1)).getpixel((0, 0))
                book["cover_color"] = avg_color  # RGB tuple

        except Exception as e:
            print(f"❌ Error processing book ID {book_id}: {e}")
            book["cover_path"] = ""
            failed += 1
    else:
        print(f"❌ Missing original cover for book ID {book_id}")
        book["cover_path"] = ""
        failed += 1

# === SAVE UPDATED JSON ===
with open(output_json_path, "w", encoding="utf-8") as f:
    json.dump(books, f, ensure_ascii=False, indent=2)

# === SUMMARY LOG ===
print("\n✅ Cover export summary:")
print(f"   Copied/resized: {copied}")
print(f"   Skipped (already resized): {skipped}")
print(f"   Failed/missing: {failed}")
print(f"📄 JSON updated at: {output_json_path}")