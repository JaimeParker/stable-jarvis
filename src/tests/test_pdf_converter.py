"""
Test script for PDF to Markdown conversion using stable_jarvis.

Usage:
    conda activate jarvis
    python tests/test_pdf_converter.py <pdf_file>
"""

import sys
from pathlib import Path

from stable_jarvis import PDFConverter, ConversionResult, ConversionOptions

# Output folder for test results
TEMP_DIR = Path(__file__).parent.parent / "temp"


def test_basic_conversion(pdf_path: str) -> None:
    """Test basic PDF to Markdown conversion."""
    print(f"\n{'='*60}")
    print("Test: Basic PDF to Markdown Conversion")
    print(f"{'='*60}")
    
    converter = PDFConverter()
    result = converter.convert(pdf_path)
    
    if result.success:
        print(f"✓ Conversion successful")
        print(f"  Pages: {result.page_count}")
        print(f"  Title: {result.metadata.get('title', 'N/A')}")
        print(f"  Author: {result.metadata.get('author', 'N/A')}")
        print(f"\n  First 500 chars of markdown:")
        print(f"  {'-'*40}")
        print(result.markdown[:500] if result.markdown else "No content")
    else:
        print(f"✗ Conversion failed: {result.error}")


def test_save_markdown_and_images(pdf_path: str) -> None:
    """Test conversion with markdown and images saved to temp folder."""
    print(f"\n{'='*60}")
    print("Test: Save Markdown and Images to temp/")
    print(f"{'='*60}")
    
    # Create temp directory and images subdirectory
    TEMP_DIR.mkdir(exist_ok=True)
    images_dir = TEMP_DIR / "images"
    images_dir.mkdir(exist_ok=True)
    
    converter = PDFConverter()
    
    # Convert with image extraction
    options = ConversionOptions(
        write_images=True,
        image_path=str(images_dir),
        image_format="png",
        image_dpi=150,
    )
    
    result = converter.convert(pdf_path, options)
    
    if result.success:
        # Save markdown to file
        md_path = TEMP_DIR / "output.md"
        md_path.write_text(result.markdown, encoding="utf-8")
        print(f"✓ Markdown saved to: {md_path}")
        print(f"  Length: {len(result.markdown)} characters")
        
        # Check for extracted images
        image_files = list(images_dir.glob("*.png"))
        print(f"✓ Images saved to: {images_dir}")
        print(f"  Found {len(image_files)} images")
        for img in image_files[:5]:  # Show first 5 images
            print(f"    - {img.name}")
        if len(image_files) > 5:
            print(f"    ... and {len(image_files) - 5} more")
    else:
        print(f"✗ Conversion failed: {result.error}")


def test_page_selection(pdf_path: str) -> None:
    """Test converting specific pages."""
    print(f"\n{'='*60}")
    print("Test: Page Selection (first page only)")
    print(f"{'='*60}")
    
    converter = PDFConverter()
    result = converter.convert_pages(pdf_path, pages=[0])
    
    if result.success:
        print(f"✓ First page converted successfully")
        print(f"  Length: {len(result.markdown)} characters" if result.markdown else "  No content")
    else:
        print(f"✗ Conversion failed: {result.error}")


def test_chunked_conversion(pdf_path: str) -> None:
    """Test per-page chunk conversion (useful for RAG)."""
    print(f"\n{'='*60}")
    print("Test: Chunked Conversion (per-page)")
    print(f"{'='*60}")
    
    converter = PDFConverter()
    result = converter.convert_to_chunks(pdf_path)
    
    if result.success and result.chunks:
        print(f"✓ Chunked conversion successful")
        print(f"  Total chunks: {len(result.chunks)}")
        for i, chunk in enumerate(result.chunks[:3]):  # Show first 3 chunks
            text = chunk.get("text", chunk.get("md", ""))
            print(f"\n  Chunk {i+1} (first 200 chars):")
            print(f"  {text[:200]}...")
    else:
        print(f"✗ Conversion failed: {result.error}")


def test_metadata_extraction(pdf_path: str) -> None:
    """Test metadata extraction."""
    print(f"\n{'='*60}")
    print("Test: Metadata Extraction")
    print(f"{'='*60}")
    
    converter = PDFConverter()
    metadata = converter.get_metadata(pdf_path)
    
    print(f"✓ Metadata extracted:")
    for key, value in metadata.items():
        if value:  # Only show non-empty values
            print(f"  {key}: {value}")


def test_plain_text_extraction(pdf_path: str) -> None:
    """Test plain text extraction."""
    print(f"\n{'='*60}")
    print("Test: Plain Text Extraction")
    print(f"{'='*60}")
    
    converter = PDFConverter()
    text = converter.extract_text(pdf_path, pages=[0])
    
    print(f"✓ Plain text extracted from page 1:")
    print(f"  Length: {len(text)} characters")
    print(f"  First 500 chars:")
    print(f"  {'-'*40}")
    print(text[:500])


def main():
    # Default test PDF path
    PDF_PATH = (
        r"D:\Documents\Zotero\storage\SNX599P2"
        r"\Liu 等 - 2025 - RESC A Reinforcement Learning Based Search-to-Control"
        r" Planning Framework for Agile Quadrotors.pdf"
    )
    
    # Use command line argument if provided, otherwise use default
    pdf_path = sys.argv[1] if len(sys.argv) > 1 else PDF_PATH
    
    if not Path(pdf_path).exists():
        print(f"Error: File not found: {pdf_path}")
        sys.exit(1)
    
    print(f"\nTesting PDF Converter with: {pdf_path}")
    
    # Run all tests
    test_metadata_extraction(pdf_path)
    test_basic_conversion(pdf_path)
    test_save_markdown_and_images(pdf_path)
    test_page_selection(pdf_path)
    test_chunked_conversion(pdf_path)
    test_plain_text_extraction(pdf_path)
    
    print(f"\n{'='*60}")
    print("All tests completed!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
