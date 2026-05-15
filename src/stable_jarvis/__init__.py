"""
stable-jarvis: A modular toolkit for academic research automation.

Modules:
    - annotation: Programmatic PDF annotation via Zotero Web API
    - report_generator: PDF to Markdown conversion using PyMuPDF4LLM

Quick Start - Annotation:
    from stable_jarvis import annotate

    result = annotate(
        pdf_path="path/to/paper.pdf",
        attachment_key="ABC12345",
        target_text="text to highlight",
        comment="My note",
    )

Quick Start - PDF Conversion:
    from stable_jarvis import PDFConverter

    converter = PDFConverter()
    result = converter.convert("paper.pdf")

    if result.success:
        print(result.markdown)
"""

from pathlib import Path
from dotenv import load_dotenv

# Load stable-jarvis/.env so all submodules inherit the config
_load_dotenv_path = Path(__file__).resolve().parents[2] / ".env"
if _load_dotenv_path.exists():
    load_dotenv(_load_dotenv_path)

# Re-export annotation module's public API for backward compatibility
from .annotation import (
    annotate,
    ZoteroAnnotator,
    AnnotationResult,
    ZoteroConfig,
    get_default_config,
    ConfigurationError,
    CoordinateExtractor,
    TextMatch,
    ZoteroClient,
    AnnotationPayload,
)

# Re-export PDF info utility
from .annotation.coordinates import PDFInfo, get_pdf_info

# Re-export report_generator module's public API
from .report_generator import (
    PDFConverter,
    ConversionResult,
    ConversionOptions,
    ImageInfo,
    ImageQuality,
    ImageMetadata,
    markdown_to_html,
)

from .notion_to_obsidian import (
    NotionPageMigrator,
    MigrationResult,
    NotionMigrationManager,
)

from .paper_finder import (
    find_papers,
    PaperFinderConfig,
)

__all__ = [
    # Main API - Annotation
    "annotate",
    "ZoteroAnnotator",
    "AnnotationResult",
    # Main API - PDF Conversion
    "PDFConverter",
    "ConversionResult",
    "ConversionOptions",
    "ImageInfo",
    "ImageQuality",
    "ImageMetadata",
    # Main API - Notion Migration
    "NotionPageMigrator",
    "MigrationResult",
    "NotionMigrationManager",
    # Main API - Paper Finder
    "find_papers",
    "PaperFinderConfig",
    # Configuration
    "ZoteroConfig",
    "get_default_config",
    "ConfigurationError",
    # Low-level components
    "CoordinateExtractor",
    "TextMatch",
    "ZoteroClient",
    "AnnotationPayload",
    # PDF utilities
    "PDFInfo",
    "get_pdf_info",
]

__version__ = "0.2.0"
