#!/usr/bin/env python3
"""
kindle_highlights_to_pdf.py — Kindle highlights → PDF annotations

Reads your Kindle 'My Clippings.txt' file and transfers all highlights
for a given book as real PDF annotations into the local PDF file.

Usage:
    python3 kindle_highlights_to_pdf.py "My Clippings.txt" "Book.pdf"
    python3 kindle_highlights_to_pdf.py "My Clippings.txt" "Book.pdf" -v
    python3 kindle_highlights_to_pdf.py "My Clippings.txt" "Book.pdf" --list-books
"""

import argparse
import re
import sys
from pathlib import Path
from datetime import datetime

try:
    import fitz  # PyMuPDF
except ImportError:
    sys.exit("Error: PyMuPDF is not installed. Please run: pip install pymupdf")

# Default highlight color (yellow)
DEFAULT_COLOR = (1.0, 0.93, 0.0)

# Clippings entry separator
SEPARATOR = "=========="


# ── Parse My Clippings.txt ────────────────────────────────────────────────────

def parse_clippings(clippings_path: Path) -> dict[str, list[dict]]:
    """
    Parse Kindle's My Clippings.txt and return a dict mapping
    book title → list of highlight dicts: {text, page, location, date}.
    """
    content = clippings_path.read_text(encoding="utf-8-sig")  # handle BOM
    entries = content.split(SEPARATOR)

    books: dict[str, list[dict]] = {}

    for entry in entries:
        lines = [l.strip() for l in entry.strip().splitlines() if l.strip()]
        if len(lines) < 3:
            continue

        title_line = lines[0]
        meta_line = lines[1]
        highlight_text = " ".join(lines[2:])

        # Only process highlights (skip bookmarks and notes)
        if "Highlight" not in meta_line and "highlight" not in meta_line:
            continue

        if not highlight_text:
            continue

        # Extract page number if available
        page_match = re.search(r"[Pp]age (\d+)", meta_line)
        page = int(page_match.group(1)) if page_match else None

        # Extract location
        loc_match = re.search(r"[Ll]ocation (\d+)", meta_line)
        location = int(loc_match.group(1)) if loc_match else None

        books.setdefault(title_line, []).append({
            "text": highlight_text,
            "page": page,
            "location": location,
        })

    return books


def list_books(books: dict[str, list[dict]]) -> None:
    print(f"\nFound {len(books)} book(s) in clippings:\n")
    for i, (title, highlights) in enumerate(sorted(books.items()), 1):
        print(f"  {i:3}. [{len(highlights):3} highlights] {title}")
    print()


def find_best_match(books: dict[str, list[dict]], pdf_path: Path) -> tuple[str, list[dict]] | None:
    """
    Find the book in clippings that best matches the PDF filename.
    """
    pdf_stem = pdf_path.stem.lower()

    best_title, best_score = None, 0
    for title in books:
        title_lower = title.lower()
        # Count matching words
        words = re.findall(r"\w+", pdf_stem)
        score = sum(1 for w in words if len(w) > 3 and w in title_lower)
        if score > best_score:
            best_score = score
            best_title = title

    if best_title and best_score > 0:
        return best_title, books[best_title]
    return None


# ── Text search in PDF ────────────────────────────────────────────────────────

def find_text_on_page(page: fitz.Page, text: str) -> list[fitz.Rect]:
    """
    Find all rects covering the full span of text on the page.
    Tries progressively shorter prefixes to handle hyphenation.
    """
    words = text.split()
    if not words:
        return []

    # Short texts: direct search
    if len(words) <= 3:
        rects = page.search_for(text)
        if rects:
            return rects
        rects = page.search_for(text.rstrip(".,;:"))
        return rects if rects else []

    # Find start using prefix
    start_rect = None
    for n in range(min(8, len(words)), 2, -1):
        fragment = " ".join(words[:n])
        found = page.search_for(fragment)
        if found:
            start_rect = found[0]
            break

    if not start_rect:
        return []

    y_start = start_rect.y0

    # Find end using suffix
    end_rect = None
    for n in range(min(8, len(words)), 2, -1):
        fragment = " ".join(words[-n:])
        found = page.search_for(fragment)
        if found and found[-1].y1 >= y_start:
            end_rect = found[-1]
            break

    y_end = end_rect.y1 if end_rect else start_rect.y1

    # Collect all word rects between start and end
    raw_words = page.get_text("words")
    line_map: dict[float, fitz.Rect] = {}
    for w in raw_words:
        x0, y0, x1, y1 = w[0], w[1], w[2], w[3]
        if y0 >= y_start - 2 and y1 <= y_end + 2:
            key = round(y0, 1)
            r = fitz.Rect(x0, y0, x1, y1)
            line_map[key] = line_map[key] | r if key in line_map else r

    return list(line_map.values())


# ── Add annotation ────────────────────────────────────────────────────────────

def add_highlight(page: fitz.Page, rects: list[fitz.Rect], color: tuple = DEFAULT_COLOR):
    if not rects:
        return
    annot = page.add_highlight_annot(rects)
    annot.set_colors(stroke=color)
    annot.update()


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Transfer Kindle highlights (My Clippings.txt) as annotations into a local PDF."
    )
    parser.add_argument("clippings", help="Path to Kindle's 'My Clippings.txt'")
    parser.add_argument("pdf", nargs="?", help="Local PDF file (optional if --list-books)")
    parser.add_argument("-o", "--output", help="Output file (default: <pdf>_highlights.pdf)")
    parser.add_argument("-b", "--book", help="Book title to use (substring match, case-insensitive)")
    parser.add_argument("--list-books", action="store_true", help="List all books found in clippings and exit")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print each highlight with result")
    args = parser.parse_args()

    clippings_path = Path(args.clippings).expanduser().resolve()
    if not clippings_path.exists():
        sys.exit(f"Clippings file not found: {clippings_path}")

    print(f"Reading: {clippings_path.name}")
    books = parse_clippings(clippings_path)

    if not books:
        sys.exit("No highlights found in clippings file.")

    if args.list_books:
        list_books(books)
        return

    if not args.pdf:
        parser.error("PDF path is required unless --list-books is used.")

    pdf_path = Path(args.pdf).expanduser().resolve()
    if not pdf_path.exists():
        sys.exit(f"PDF file not found: {pdf_path}")

    # Select book
    if args.book:
        query = args.book.lower()
        matches = [(t, h) for t, h in books.items() if query in t.lower()]
        if not matches:
            sys.exit(f"No book found matching: {args.book}\nUse --list-books to see all titles.")
        title, highlights = matches[0]
        if len(matches) > 1:
            print(f"Multiple matches, using: {title}")
    else:
        result = find_best_match(books, pdf_path)
        if not result:
            print("Could not auto-match book. Use --list-books and -b <title>.")
            list_books(books)
            sys.exit(1)
        title, highlights = result
        print(f"Auto-matched book: {title}")

    print(f"Highlights: {len(highlights)}")

    output_path = (
        Path(args.output).expanduser().resolve()
        if args.output
        else pdf_path.parent / (pdf_path.stem + "_highlights.pdf")
    )

    doc = fitz.open(pdf_path)
    print(f"PDF: {pdf_path.name} ({doc.page_count} pages)")

    done, not_found = 0, []

    for h in highlights:
        text = h["text"]
        page_hint = h["page"]

        # Build search order: page hint ± tolerance, then full scan
        if page_hint and 1 <= page_hint <= doc.page_count:
            search_order = [page_hint - 1 + d for d in [0, -1, 1, -2, 2]
                            if 0 <= page_hint - 1 + d < doc.page_count]
        else:
            search_order = list(range(min(doc.page_count, 50)))  # scan first 50 pages

        found = False
        for page_idx in search_order:
            rects = find_text_on_page(doc[page_idx], text)
            if rects:
                add_highlight(doc[page_idx], rects)
                done += 1
                found = True
                if args.verbose:
                    print(f"  ✓ p.{page_idx + 1}: {text[:60]}")
                break

        if not found:
            not_found.append(h)
            if args.verbose:
                print(f"  ✗ NOT FOUND: {text[:60]}")

    print(f"\nResult: {done}/{len(highlights)} highlights transferred.")
    if not_found:
        print(f"Not found ({len(not_found)}):")
        for h in not_found:
            print(f"  {h['text'][:80]}")

    doc.save(output_path, garbage=4, deflate=True)
    doc.close()
    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    main()
