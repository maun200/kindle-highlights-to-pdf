# kindle-highlights-to-pdf

**Transfer your Kindle highlights directly into your PDF** — as real, standard-compliant PDF annotations, compatible with Zotero, Citavi, Adobe Acrobat, Okular, and every other PDF reader.

[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![Donate via PayPal](https://img.shields.io/badge/Donate-PayPal-blue.svg)](https://www.paypal.com/donate/?business=m.gruda%40web.de&currency_code=EUR)

> If this tool saves you time, consider buying me a coffee ☕  
> **[➡ Donate via PayPal](https://www.paypal.com/donate/?business=m.gruda%40web.de&currency_code=EUR)**

---

## What it does

When you highlight text on your Kindle, those highlights are stored only inside Amazon's ecosystem. This tool reads your `My Clippings.txt` file and writes every highlight back into the corresponding local PDF as a proper annotation — so your highlights appear in Zotero, Citavi, Acrobat, and any other PDF reader.

**Also check out:** [speechify-to-pdf](https://github.com/maun200/speechify_to_pdf) — the same idea for Speechify users.

## Requirements

```bash
pip install pymupdf
```

Python 3.10 or newer.

## Quick Start

### 1. Get your Kindle clippings

Connect your Kindle via USB. The file is at:
```
Kindle/documents/My Clippings.txt
```
Copy it to your computer.

### 2. Run the script

```bash
python3 kindle_highlights_to_pdf.py "My Clippings.txt" "Book.pdf"
```

This creates `Book_highlights.pdf` in the same folder as your PDF.

**See all books in your clippings:**
```bash
python3 kindle_highlights_to_pdf.py "My Clippings.txt" --list-books
```

**Select a specific book by title:**
```bash
python3 kindle_highlights_to_pdf.py "My Clippings.txt" "Book.pdf" -b "Sapiens"
```

**Custom output path:**
```bash
python3 kindle_highlights_to_pdf.py "My Clippings.txt" "Book.pdf" -o "Book_annotated.pdf"
```

**Verbose output (see each highlight):**
```bash
python3 kindle_highlights_to_pdf.py "My Clippings.txt" "Book.pdf" -v
```

## How it works

1. Parses `My Clippings.txt` — Kindle's plain-text highlight export
2. Auto-matches the book title to your PDF filename
3. Searches each highlight text in the PDF using fuzzy prefix matching
4. Writes standard PDF highlight annotations using PyMuPDF

## Limitations

- **Page numbers:** Kindle's clippings use Kindle locations, not always page numbers. The script uses the page number when available and falls back to a full-document search.
- **Scanned PDFs:** No text layer = no searchable text = highlights can't be placed.
- **Very long highlights:** Very long ones may not match if the PDF has different line breaks.
- **DRM-protected PDFs:** Only works with DRM-free PDFs you own locally.

## Troubleshooting

**"No highlights found"**
→ Make sure the file is `My Clippings.txt` from your Kindle, not a different export.

**"Could not auto-match book"**
→ Use `--list-books` to see all titles, then `-b "partial title"` to select.

**`ModuleNotFoundError: No module named 'fitz'`**
→ Run `pip install pymupdf`.

## Roadmap

- [ ] GUI (drag-and-drop) for non-technical users
- [ ] Standalone executable (.exe / .app)
- [ ] Color coding by Kindle highlight color
- [ ] Export highlights to Markdown / Obsidian

## Contributing

Pull requests and issue reports are welcome! Please open an issue before starting work on larger changes.

## Support the project

This tool is free and open-source. If it saves you time, a small donation helps:

**[☕ Donate via PayPal](https://www.paypal.com/donate/?business=m.gruda%40web.de&currency_code=EUR)**

## License

MIT
