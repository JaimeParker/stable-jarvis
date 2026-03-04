# Added Image Extraction with Position Metadata

### New Features
- **Image extraction with position metadata**: Extract images from PDFs with bounding box and position information
  - `ImageMetadata` dataclass: stores filename, page, bbox, position, description
  - `extract_images_with_metadata()` method: extracts images and computes position using `page.get_image_bbox()`
  - `save_image_manifest()` method: saves metadata to JSON manifest file
  - `_get_position_description()` helper: converts bbox to human-readable position (top/center/bottom + left/center/right)

### Usage
```python
from stable_jarvis_dev import PDFConverter

converter = PDFConverter()

# Extract images with position metadata
metadata = converter.extract_images_with_metadata(
    "paper.pdf",
    "./figures",
    quality="high",
    name_prefix="SNX599P2",
)

# Save manifest JSON
converter.save_image_manifest(metadata, "./figures/manifest.json")

# Output format:
# [{"filename": "SNX599P2_fig1.png", "page": 1, "description": "Figure at the top of page 1"}, ...]
```

### Files Modified
- `stable_jarvis_dev/report_generator/converter.py`: Added `ImageMetadata`, `extract_images_with_metadata()`, `save_image_manifest()`
- `stable_jarvis_dev/report_generator/__init__.py`: Export `ImageMetadata`
- `stable_jarvis_dev/__init__.py`: Export `ImageMetadata`

### Files Added
- `tests/test_image_manifest.py`

---

# Added report_generator submodule

### New Features
- **report_generator submodule**: PDF to Markdown conversion using PyMuPDF4LLM
  - `PDFConverter` class with high-level API for conversion
  - `ConversionOptions` dataclass for configuring output (images, OCR, chunks, etc.)
  - `ConversionResult` dataclass with success status, markdown/chunks, and metadata
  - `ImageInfo` dataclass for extracted image information
  - `ImageQuality` enum for quality filtering (low/medium/high/epic)
  - Methods: `convert()`, `convert_pages()`, `convert_to_chunks()`, `extract_text()`, `get_metadata()`, `extract_images()`, `list_images()`

### Files Added
- `stable_jarvis_dev/report_generator/__init__.py`
- `stable_jarvis_dev/report_generator/converter.py`
- `stable_jarvis_dev/report_generator/py.typed`
- `tests/test_pdf_converter.py`

### Usage
```python
from stable_jarvis_dev import PDFConverter, ConversionOptions

converter = PDFConverter()
result = converter.convert("paper.pdf")

if result.success:
    print(result.markdown)

# With options:
result = converter.convert(
    "paper.pdf",
    options=ConversionOptions(
        pages=[0, 1, 2],
        write_images=True,
        image_path="./images",
    )
)

# Per-page chunks (for RAG):
result = converter.convert_to_chunks("paper.pdf")
for chunk in result.chunks:
    print(chunk)
```

---

# MISSION: Cyber Brain Proof of Concept 1 (Coordinate & Injection Handshake)

Status: Done.

## Background
You are an expert Python AI agent with deep knowledge of PDF processing and REST APIs. We are building an autonomous "Cyber Brain" for academic research. 
Our current goal (PoC 1) is to prove that we can programmatically highlight text in a PDF stored in Zotero **without modifying the physical PDF file**. We will do this by calculating text coordinates using `PyMuPDF` and injecting native annotation metadata via the `Zotero Web API`.

## Your Task
Write and execute a standalone Python script (`test_zotero_highlight.py`) under `scripts` folder to perform the following exact steps:

1. **Setup**: The user will provide a path to a local dual-column PDF paper, its Zotero Attachment Key, their Zotero API Key, and Library ID. Hardcode these as variables at the top of the script for testing.
2. **Coordinate Extraction**:
   * Use `pymupdf` to open the local PDF.
   * Search for a specific sentence provided by the user (e.g., an equation description).
   * Get the bounding box `[x0, y0, x1, y1]`.
3. **Coordinate Transformation (The Core Challenge)**:
   * **WARNING**: PyMuPDF's origin is Top-Left. Zotero's internal reader *might* use Bottom-Left (Standard PDF space) or Top-Left. 
   * You need to output the raw PyMuPDF coordinates, and you will construct the Zotero payload. **Your primary goal is to figure out the correct mathematical mapping** so the highlight visually aligns perfectly over the text in the Zotero UI. (Hint: Try passing raw PyMuPDF coordinates first. If it's upside down in Zotero, implement `y_new = page_height - y_old`).
4. **API Injection**:
   * Use `pyzotero` to create a new item of `itemType: "annotation"`.
   * Set the `parentItem` to the PDF Attachment Key.
   * Format the `annotationPosition` as a JSON string containing the `pageIndex` and mapped `rects`.
   * Upload the annotation.
5. **Verification Loop**:
   * The user will open their local Zotero app, let it sync, and manually check if the highlight appears exactly over the target sentence.
   * If the highlight is misplaced (e.g., floating in the wrong place, inverted, or offset), the user will tell you. You must then adjust your coordinate transformation logic in the script and re-run.

## Strict Constraints
* **DO NOT** use `page.add_highlight_annot()` or save/modify the original PDF file. The file hash must remain unchanged.
* Read the provided `pymupdf_guide.md` and `pyzotero_annotation_guide.md` for API usage syntax.

Start by writing the initial `test_zotero_highlight.py` script and ask the user to provide the required ID/Keys and the target text sentence.

## Zotero Credentials

**IMPORTANT**: All agents and scripts MUST read Zotero credentials (library_id, api_key, library_type) from `user_info/zotero.json` only. Never hardcode these values in scripts.

Example usage:
```python
import json
from pathlib import Path

_script_dir = Path(__file__).resolve().parent
_zotero_config_path = _script_dir.parent / "user_info" / "zotero.json"
with open(_zotero_config_path, "r", encoding="utf-8") as f:
    _zotero_config = json.load(f)

LIBRARY_ID   = _zotero_config["library_id"]
API_KEY      = _zotero_config["api_key"]
LIBRARY_TYPE = _zotero_config["library_type"]
```

## Test

The test paper is stored locally at `D:\Documents\Zotero\storage\SNX599P2\Liu 等 - 2025 - RESC A Reinforcement Learning Based Search-to-Control Planning Framework for Agile Quadrotors.pdf`, `SNX599P2` is the Attachment Key.

You can add a annotation to the sentence `However, trajectory optimization methods typically decouple planning and control`

# Reconstruct and Create Stable-JARVIS-Dev 0.1.0

Status: Done.

## Summary

Restructured the project as a modern Python package with proper `pyproject.toml` configuration, enabling `pip install -e .` and clean imports via `from stable_jarvis_dev import ...`.

## Changes

### Package Structure
- Created `src/stable_jarvis_dev/` directory (renamed from `src/auto-annotation/` to fix Python import compatibility — hyphens are invalid in Python identifiers)
- Added `pyproject.toml` with PEP 621 metadata, dependencies (`pymupdf`, `pymupdf4llm`, `pyzotero`), and `src/` layout configuration
- Added minimal `setup.py` shim for older pip compatibility
- Added `py.typed` marker for type checker support
- Removed old `src/auto-annotation/` directory

### Configuration System
- Refactored `config.py` with flexible configuration loading:
  1. **Priority 1**: Environment variables (`ZOTERO_LIBRARY_ID`, `ZOTERO_API_KEY`, `ZOTERO_LIBRARY_TYPE`)
  2. **Priority 2**: Config file search (`./zotero.json` → `./user_info/zotero.json` → `~/.config/stable-jarvis-dev/zotero.json`)
- Added `ConfigurationError` exception with helpful error messages
- Added `ZoteroConfig.from_env()` class method

### Test Updates
- Updated `tests/test_zotero_highlight.py` to use standard imports instead of `importlib.util` workaround
- Updated `tests/find_attachment_key.py` to use package imports
- Added `tests/__init__.py` for pytest discovery

### Documentation
- Updated `README.md` with installation instructions and configuration options
- Added `.vscode/settings.json` to exclude `__pycache__` and `*.egg-info` from IDE

## Usage

```bash
# Install in editable mode
conda activate jarvis
pip install -e .

# Import the package
python -c "from stable_jarvis_dev import ZoteroAnnotator; print('OK')"
```

## Verification

```
$ pip show stable-jarvis-dev
Name: stable-jarvis-dev
Version: 0.1.0
Summary: Programmatic PDF annotation injection via Zotero Web API
Requires: pymupdf, pymupdf4llm, pyzotero
```

Test script `tests/test_zotero_highlight.py` runs successfully with the new package structure.

# Restructure to Modular Package Layout

Status: Done.

## Summary

Restructured the package from `src/stable_jarvis_dev/` to a modular layout at `stable_jarvis_dev/annotation/`, preparing for future submodules.

## Changes

### New Structure
```
stable_jarvis_dev/
├── __init__.py              # Top-level re-exports (backward compatible)
├── py.typed
└── annotation/              # Annotation submodule
    ├── __init__.py
    ├── annotator.py
    ├── config.py
    ├── coordinates.py
    ├── zotero_client.py
    └── py.typed
```

### Import Options
```python
# Top-level import (backward compatible)
from stable_jarvis_dev import ZoteroAnnotator, annotate

# Submodule import (explicit)
from stable_jarvis_dev.annotation import ZoteroAnnotator, annotate
```

### pyproject.toml Update
- Changed `[tool.setuptools.packages.find]` from `where = ["src"]` to `where = ["."]` with `include = ["stable_jarvis_dev*"]`

### Cleanup
- Removed old `src/` directory

## Verification

Test passed with annotation key `8QXQRAMC` created successfully.

