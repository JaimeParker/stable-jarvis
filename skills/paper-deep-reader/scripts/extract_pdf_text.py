#!/usr/bin/env python3
"""Extract paper content from a PDF using stable_jarvis.PDFConverter.

Defaults to Markdown output (preserves headings, LaTeX, structure).
Use --plain for plain text fallback.

Usage:
    python extract_pdf_text.py --pdf path/to/paper.pdf [--output path/to/paper.md]
    python extract_pdf_text.py --pdf path/to/paper.pdf --plain     # plain text
    python extract_pdf_text.py --pdf path/to/paper.pdf --page-count  # page count only

If --output is omitted, prints to stdout.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path

from stable_jarvis import PDFConverter


def main():
    ap = argparse.ArgumentParser(description="Extract content from PDF")
    ap.add_argument("--pdf", required=True, type=Path, help="Path to PDF file")
    ap.add_argument("--output", "-o", type=Path, default=None, help="Output file path")
    ap.add_argument("--plain", action="store_true", help="Output plain text instead of Markdown")
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

    if args.plain:
        text = converter.extract_text(args.pdf)
    else:
        result = converter.convert(args.pdf)
        if not result.success:
            print(f"Error: Markdown conversion failed, falling back to plain text", file=sys.stderr)
            text = converter.extract_text(args.pdf)
        else:
            text = result.markdown

    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(text, encoding="utf-8")
        print(f"Extracted {len(text):,} chars → {args.output}", file=sys.stderr)
    else:
        print(text)


if __name__ == "__main__":
    main()
