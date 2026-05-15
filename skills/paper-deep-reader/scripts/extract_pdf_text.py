#!/usr/bin/env python3
"""Extract plain text from a PDF using pymupdf (fallback: pdfplumber).

Usage:
    python extract_pdf_text.py --pdf path/to/paper.pdf [--output path/to/output.txt]
    python extract_pdf_text.py --pdf path/to/paper.pdf --page-count    # only report page count

If --output is omitted, prints to stdout.
"""
from __future__ import annotations
import argparse
import re
import sys
from pathlib import Path


def extract_text(pdf_path: Path) -> str:
    try:
        return _extract_pymupdf(pdf_path)
    except Exception:
        return _extract_pdfplumber(pdf_path)


def count_pages(pdf_path: Path) -> int:
    try:
        import fitz
        doc = fitz.open(str(pdf_path))
        n = len(doc)
        doc.close()
        return n
    except Exception:
        return -1


def _extract_pymupdf(pdf_path: Path) -> str:
    import fitz
    doc = fitz.open(str(pdf_path))
    pages = [page.get_text("text") for page in doc]
    doc.close()
    return _clean("\n".join(pages))


def _extract_pdfplumber(pdf_path: Path) -> str:
    import pdfplumber
    with pdfplumber.open(str(pdf_path)) as pdf:
        pages = [p.extract_text() or "" for p in pdf.pages]
    return _clean("\n".join(pages))


def _clean(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = text.replace("\f", "\n")
    return text.strip()


def main():
    ap = argparse.ArgumentParser(description="Extract text from PDF")
    ap.add_argument("--pdf", required=True, type=Path, help="Path to PDF file")
    ap.add_argument("--output", "-o", type=Path, default=None, help="Output text file path")
    ap.add_argument("--page-count", action="store_true", help="Only print page count and exit")
    args = ap.parse_args()

    if not args.pdf.exists():
        print(f"Error: PDF not found: {args.pdf}", file=sys.stderr)
        sys.exit(1)

    if args.page_count:
        print(count_pages(args.pdf))
        return

    text = extract_text(args.pdf)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(f"Extracted {len(text):,} chars → {args.output}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
