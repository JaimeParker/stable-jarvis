#!/usr/bin/env python3
"""Extract plain text from a PDF using stable_jarvis.PDFConverter.

Usage:
    python extract_pdf_text.py --pdf path/to/paper.pdf [--output path/to/output.txt]
    python extract_pdf_text.py --pdf path/to/paper.pdf --page-count    # only report page count

If --output is omitted, prints to stdout.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from stable_jarvis import PDFConverter


def main():
    ap = argparse.ArgumentParser(description="Extract text from PDF")
    ap.add_argument("--pdf", required=True, type=Path, help="Path to PDF file")
    ap.add_argument("--output", "-o", type=Path, default=None, help="Output text file path")
    ap.add_argument("--page-count", action="store_true", help="Only print page count and exit")
    args = ap.parse_args()

    if not args.pdf.exists():
        print(f"Error: PDF not found: {args.pdf}", file=sys.stderr)
        sys.exit(1)

    converter = PDFConverter()

    if args.page_count:
        metadata = converter.get_metadata(args.pdf)
        print(metadata.get("page_count", -1))
        return

    text = converter.extract_text(args.pdf)
    if args.output:
        args.output.write_text(text, encoding="utf-8")
        print(f"Extracted {len(text):,} chars → {args.output}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
