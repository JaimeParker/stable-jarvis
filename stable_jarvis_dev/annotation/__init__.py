"""
Annotation submodule: Programmatic PDF annotation via Zotero Web API.

This module provides tools to:
1. Extract text coordinates from PDF files using PyMuPDF
2. Inject annotations into Zotero without modifying the PDF file
"""

from .annotator import AnnotationResult, ZoteroAnnotator, annotate
from .config import ConfigurationError, ZoteroConfig, get_default_config
from .coordinates import CoordinateExtractor, TextMatch
from .zotero_client import AnnotationPayload, ZoteroClient

__all__ = [
    # Main API
    "annotate",
    "ZoteroAnnotator",
    "AnnotationResult",
    # Configuration
    "ZoteroConfig",
    "get_default_config",
    "ConfigurationError",
    # Low-level components
    "CoordinateExtractor",
    "TextMatch",
    "ZoteroClient",
    "AnnotationPayload",
]
