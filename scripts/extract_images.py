"""
CLI wrapper for PDF image extraction.

Usage:
    python scripts/extract_images.py <pdf_path> <output_dir> [options]

Examples:
    python scripts/extract_images.py "D:\\path\\to\\paper.pdf" "./output"
    python scripts/extract_images.py "D:\\paper.pdf" "./images" --quality high --prefix ABC123
    python scripts/extract_images.py "D:\\paper.pdf" "./images" --list-only
"""

import argparse
import sys
from pathlib import Path

from stable_jarvis_dev import PDFConverter, ImageQuality


def main():
    parser = argparse.ArgumentParser(
        description="Extract images from a PDF file with quality filtering.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Quality levels (minimum dimensions):
  any:    No filtering (all images)
  low:    100x100
  medium: 200x200
  high:   400x400

Examples:
  python scripts/extract_images.py "D:\\paper.pdf" "./output"
  python scripts/extract_images.py "D:\\paper.pdf" "./images" --quality high --prefix ABC123
  python scripts/extract_images.py "D:\\paper.pdf" "./images" --list-only
        """,
    )
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument(
        "output_dir",
        nargs="?",
        default="./extracted_images",
        help="Output directory for extracted images (default: ./extracted_images)",
    )
    parser.add_argument(
        "--quality", "-q",
        choices=["any", "low", "medium", "high"],
        default="high",
        help="Minimum quality level for extracted images (default: high)",
    )
    parser.add_argument(
        "--prefix", "-p",
        default="",
        help="Filename prefix for extracted images (e.g., attachment key)",
    )
    parser.add_argument(
        "--list-only", "-l",
        action="store_true",
        help="Only list images without extracting",
    )

    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return 1

    converter = PDFConverter()

    # List all images
    print(f"PDF: {pdf_path.name}")
    print("=" * 60)
    
    all_images = converter.list_images(str(pdf_path))
    print(f"Total images found: {len(all_images)}")
    for img in all_images:
        print(f"  Page {img.page+1}: {img.width}x{img.height} ({img.colorspace})")

    if args.list_only:
        print("\nQuality level thresholds:")
        for q in ImageQuality:
            print(f"  {q.name}: {q.min_width}x{q.min_height}")
        return 0

    # Extract images
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"\nExtracting images (quality={args.quality})...")
    images = converter.extract_images(
        str(pdf_path),
        output_dir,
        quality=args.quality,
        name_prefix=args.prefix if args.prefix else None,
    )

    print(f"\nExtracted {len(images)} images to {output_dir}")
    for img in images:
        print(f"  Page {img.page+1}: {img.width}x{img.height} -> {Path(img.file_path).name}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
