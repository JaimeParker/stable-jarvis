"""
Test image extraction with metadata and manifest generation.
"""

from pathlib import Path
import json

from stable_jarvis import PDFConverter, ImageMetadata


def main():
    # Test PDF path
    pdf_path = Path(r"D:\Documents\Zotero\storage\SNX599P2\Liu 等 - 2025 - RESC A Reinforcement Learning Based Search-to-Control Planning Framework for Agile Quadrotors.pdf")
    
    if not pdf_path.exists():
        print(f"Test PDF not found: {pdf_path}")
        return
    
    # Output directory
    output_dir = Path("test_output/manifest_test")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"PDF: {pdf_path.name}")
    print(f"Output: {output_dir}")
    print("=" * 70)
    
    # Create converter
    converter = PDFConverter()
    
    # Extract images with metadata
    print("\nExtracting images with metadata...")
    metadata = converter.extract_images_with_metadata(
        pdf_path,
        output_dir,
        quality="high",
        name_prefix="SNX599P2",
    )
    
    print(f"\nExtracted {len(metadata)} images:\n")
    
    # Print each image's metadata
    for i, m in enumerate(metadata, 1):
        print(f"[{i}] {m.filename}")
        print(f"    Page: {m.page + 1}")
        print(f"    Position: {m.position}")
        print(f"    BBox: ({m.bbox[0]:.1f}, {m.bbox[1]:.1f}, {m.bbox[2]:.1f}, {m.bbox[3]:.1f})")
        print(f"    Size: {m.width}x{m.height}")
        print(f"    Description: {m.description}")
        print()
    
    # Save simple manifest
    manifest_path = output_dir / "manifest.json"
    converter.save_image_manifest(metadata, manifest_path)
    print(f"Saved simple manifest to: {manifest_path}")
    
    # Show manifest content
    print("\nManifest content (simple):")
    print("-" * 40)
    with open(manifest_path, "r", encoding="utf-8") as f:
        content = json.load(f)
        for item in content:
            print(f"  {item}")
    
    # Save full manifest
    manifest_full_path = output_dir / "manifest_full.json"
    converter.save_image_manifest(metadata, manifest_full_path, include_full_details=True)
    print(f"\nSaved full manifest to: {manifest_full_path}")
    
    print("\n" + "=" * 70)
    print("Test completed!")


if __name__ == "__main__":
    main()
