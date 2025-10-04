import requests
import json
import time
from typing import List, Dict, Optional

# === CONFIGURATION ===
GOOGLE_BOOKS_API_BASE = "https://www.googleapis.com/books/v1/volumes"
REQUEST_DELAY = 0.5  # Delay between requests to avoid rate limiting


def search_google_books(title: str, author: str = None) -> Optional[Dict]:
    """
    Search for a book on Google Books API and return the first result.
    
    Args:
        title: Book title
        author: Book author (optional, improves accuracy)
    
    Returns:
        Dictionary with book information or None if not found
    """
    # Build search query
    if author:
        query = f"intitle:{title} inauthor:{author}"
    else:
        query = f"intitle:{title}"
    
    params = {
        "q": query,
        "maxResults": 1
    }
    
    try:
        response = requests.get(GOOGLE_BOOKS_API_BASE, params=params, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        
        if data.get("totalItems", 0) > 0:
            return data["items"][0]
        else:
            print(f"  ❌ No results found for: {title}")
            return None
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Error fetching data: {e}")
        return None


def extract_genre_info(book_data: Dict) -> Dict:
    """
    Extract genre/category information from Google Books API response.
    
    Args:
        book_data: Raw book data from Google Books API
    
    Returns:
        Dictionary with extracted information
    """
    volume_info = book_data.get("volumeInfo", {})
    
    return {
        "title": volume_info.get("title", "Unknown"),
        "authors": volume_info.get("authors", []),
        "categories": volume_info.get("categories", []),
        "main_category": volume_info.get("mainCategory"),
        "description": volume_info.get("description", "")[:200],  # First 200 chars
        "published_date": volume_info.get("publishedDate"),
        "isbn": extract_isbn(volume_info),
    }


def extract_isbn(volume_info: Dict) -> Optional[str]:
    """Extract ISBN from volume info."""
    identifiers = volume_info.get("industryIdentifiers", [])
    for identifier in identifiers:
        if identifier.get("type") in ["ISBN_13", "ISBN_10"]:
            return identifier.get("identifier")
    return None


def test_single_book(title: str, author: str = None):
    """Test fetching genre for a single book."""
    print(f"\n{'='*60}")
    print(f"Searching for: {title}")
    if author:
        print(f"Author: {author}")
    print('='*60)
    
    book_data = search_google_books(title, author)
    
    if book_data:
        info = extract_genre_info(book_data)
        
        print(f"\n✅ Found:")
        print(f"  Title: {info['title']}")
        print(f"  Authors: {', '.join(info['authors'])}")
        print(f"  Categories: {', '.join(info['categories']) if info['categories'] else 'None'}")
        print(f"  Main Category: {info['main_category'] or 'None'}")
        print(f"  ISBN: {info['isbn'] or 'None'}")
        print(f"  Published: {info['published_date'] or 'Unknown'}")
        if info['description']:
            print(f"  Description: {info['description']}...")
        
        return info
    else:
        print("\n❌ Book not found")
        return None


def test_multiple_books(books: List[Dict]):
    """Test fetching genres for multiple books."""
    print(f"\n{'='*60}")
    print(f"Testing {len(books)} books")
    print('='*60)
    
    results = []
    
    for i, book in enumerate(books, 1):
        print(f"\n[{i}/{len(books)}] Processing: {book['title']}")
        
        book_data = search_google_books(book['title'], book.get('author'))
        
        if book_data:
            info = extract_genre_info(book_data)
            results.append({
                "original": book,
                "found": info
            })
            
            categories = ', '.join(info['categories']) if info['categories'] else 'None'
            print(f"  ✅ Categories: {categories}")
        else:
            results.append({
                "original": book,
                "found": None
            })
            print(f"  ❌ Not found")
        
        # Rate limiting
        time.sleep(REQUEST_DELAY)
    
    return results


def print_summary(results: List[Dict]):
    """Print summary of results."""
    print(f"\n{'='*60}")
    print("SUMMARY")
    print('='*60)
    
    found = sum(1 for r in results if r['found'] is not None)
    total = len(results)
    
    print(f"\nTotal books: {total}")
    print(f"Found: {found} ({found/total*100:.1f}%)")
    print(f"Not found: {total - found}")
    
    # Count books with categories
    with_categories = sum(1 for r in results if r['found'] and r['found']['categories'])
    print(f"With categories: {with_categories} ({with_categories/total*100:.1f}%)")
    
    # Show all unique categories found
    all_categories = set()
    for result in results:
        if result['found'] and result['found']['categories']:
            all_categories.update(result['found']['categories'])
    
    if all_categories:
        print(f"\nUnique categories found ({len(all_categories)}):")
        for category in sorted(all_categories):
            print(f"  - {category}")


def save_results(results: List[Dict], filename: str = "genre_test_results.json"):
    """Save results to JSON file."""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n💾 Results saved to: {filename}")


# === MAIN TEST FUNCTION ===

def main():
    print("🚀 Book Genre API Test Script")
    print("Using Google Books API\n")
    
    # Test 1: Single book
    print("\n" + "="*60)
    print("TEST 1: Single Book")
    print("="*60)
    test_single_book("Project Hail Mary", "Andy Weir")
    
    # Test 2: Multiple books from different genres
    print("\n" + "="*60)
    print("TEST 2: Multiple Books")
    print("="*60)
    
    test_books = [
        {"title": "Dune", "author": "Frank Herbert"},
        {"title": "Pride and Prejudice", "author": "Jane Austen"},
        {"title": "The Hobbit", "author": "J.R.R. Tolkien"},
        {"title": "1984", "author": "George Orwell"},
        {"title": "The Great Gatsby", "author": "F. Scott Fitzgerald"},
        {"title": "Harry Potter and the Philosopher's Stone", "author": "J.K. Rowling"},
        {"title": "To Kill a Mockingbird", "author": "Harper Lee"},
        {"title": "The Hunger Games", "author": "Suzanne Collins"},
    ]
    
    results = test_multiple_books(test_books)
    
    # Print summary
    print_summary(results)
    
    # Save results
    save_results(results)
    
    print("\n✅ Test complete!")


if __name__ == "__main__":
    main()
