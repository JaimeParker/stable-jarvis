"""
Report Generator submodule: PDF to Markdown conversion using PyMuPDF4LLM.

This module provides tools to:
1. Convert PDF documents to clean Markdown format
2. Extract images and tables from PDFs
3. Support multi-column layouts and reading order
"""

from .converter import (
    PDFConverter,
    ConversionResult,
    ConversionOptions,
    ImageInfo,
    ImageQuality,
    ImageMetadata,
    markdown_to_html,
)

__all__ = [
    "PDFConverter",
    "ConversionResult",
    "ConversionOptions",
    "ImageInfo",
    "ImageQuality",
    "ImageMetadata",
    "markdown_to_html",
]
