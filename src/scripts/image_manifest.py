"""
CLI wrapper for PDF image extraction with metadata and manifest generation.

Usage:
    python scripts/image_manifest.py <pdf_path> <output_dir> [options]

Examples:
    python scripts/image_manifest.py "D:\\path\\to\\paper.pdf" "./output"
    python scripts/image_manifest.py "D:\\paper.pdf" "./images" --prefix ABC123 --full
"""

import argparse
import json
import sys
from pathlib import Path

from stable_jarvis import PDFConverter


def main():
    parser = argparse.ArgumentParser(
        description="Extract images from PDF with metadata and generate a manifest file.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This script extracts images along with their metadata (page, position, bbox, 
dimensions) and saves a JSON manifest file for AI agent consumption.

Examples:
  python scripts/image_manifest.py "D:\\paper.pdf" "./output"
  python scripts/image_manifest.py "D:\\paper.pdf" "./images" --prefix ABC123
  python scripts/image_manifest.py "D:\\paper.pdf" "./images" --prefix ABC123 --full
        """,
    )
    parser.add_argument("pdf_path", help="Path to the PDF file")
    parser.add_argument(
        "output_dir",
        nargs="?",
        default="./extracted_images",
        help="Output directory for images and manifest (default: ./extracted_images)",
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
        "--full", "-f",
        action="store_true",
        help="Include full details in manifest (bbox, dimensions, etc.)",
    )
    parser.add_argument(
        "--manifest-name", "-m",
        default="manifest.json",
        help="Name of the manifest file (default: manifest.json)",
    )

    args = parser.parse_args()

    pdf_path = Path(args.pdf_path)
    if not pdf_path.exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return 1

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"PDF: {pdf_path.name}")
    print(f"Output: {output_dir}")
    print("=" * 70)

    converter = PDFConverter()

    # Extract images with metadata
    print("\nExtracting images with metadata...")
    metadata = converter.extract_images_with_metadata(
        pdf_path,
        output_dir,
        quality=args.quality,
        name_prefix=args.prefix if args.prefix else None,
    )

    print(f"\nExtracted {len(metadata)} images:\n")

    # Print each image's metadata
    for i, m in enumerate(metadata, 1):
        print(f"[{i}] {m.filename}")
        print(f"    Page: {m.page + 1}")
        print(f"    Position: {m.position}")
        print(f"    Size: {m.width}x{m.height}")
        print(f"    Description: {m.description}")
        if args.full:
            print(f"    BBox: ({m.bbox[0]:.1f}, {m.bbox[1]:.1f}, {m.bbox[2]:.1f}, {m.bbox[3]:.1f})")
        print()

    # Save manifest
    manifest_path = output_dir / args.manifest_name
    converter.save_image_manifest(metadata, manifest_path, include_full_details=args.full)
    print(f"Saved manifest to: {manifest_path}")

    # Show manifest content
    print("\nManifest content:")
    print("-" * 40)
    with open(manifest_path, "r", encoding="utf-8") as f:
        content = json.load(f)
        print(json.dumps(content, indent=2))

    print("\n" + "=" * 70)
    return 0


if __name__ == "__main__":
    sys.exit(main())
