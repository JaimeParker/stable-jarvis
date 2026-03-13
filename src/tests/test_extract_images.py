"""Test high-quality image extraction."""
from pathlib import Path
from stable_jarvis import PDFConverter, ImageInfo, ImageQuality

# ─────────────────────────────────────────────
# TEST CONFIGURATION
# ─────────────────────────────────────────────
PDF_PATH = (
    r"D:\Documents\Zotero\storage\SNX599P2"
    r"\Liu 等 - 2025 - RESC A Reinforcement Learning Based Search-to-Control"
    r" Planning Framework for Agile Quadrotors.pdf"
)
ATTACHMENT_KEY = "SNX599P2"  # Used as filename prefix
OUTPUT_DIR = Path(__file__).parent.parent / "temp" / "hq_images"

converter = PDFConverter()

# List all images first
print("Listing all images in PDF:")
all_images = converter.list_images(PDF_PATH)
print(f"  Total images found: {len(all_images)}")
for img in all_images:
    print(f"  Page {img.page+1}: {img.width}x{img.height} ({img.colorspace})")

# Show quality level thresholds
print("\nQuality level thresholds:")
for q in ImageQuality:
    print(f"  {q.name}: {q.min_width}x{q.min_height}")

# Extract high-quality images with simple naming
print(f"\n{'='*60}")
print(f"Extracting images with quality='high', prefix='{ATTACHMENT_KEY}':")
print("="*60)

images = converter.extract_images(
    PDF_PATH,
    OUTPUT_DIR,
    quality="high",
    name_prefix=ATTACHMENT_KEY,  # -> SNX599P2_fig1.png, SNX599P2_fig2.png, ...
)

print(f"\nExtracted {len(images)} images to {OUTPUT_DIR}")
for img in images:
    print(f"  Page {img.page+1}: {img.width}x{img.height} -> {Path(img.file_path).name}")
