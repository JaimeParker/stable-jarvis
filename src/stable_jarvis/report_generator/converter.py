"""
PDF to Markdown converter using PyMuPDF and PyMuPDF4LLM.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import pymupdf
import pymupdf4llm


class ImageQuality(Enum):
    """
    Predefined quality levels for image extraction.
    
    Each level defines minimum width/height thresholds:
    - LOW: 100x100 - Includes small icons and thumbnails
    - MEDIUM: 300x300 - Moderate quality images
    - HIGH: 500x500 - Good quality figures (recommended for papers)
    - EPIC: 1000x1000 - Publication-quality, large figures only
    """
    LOW = (100, 100)
    MEDIUM = (300, 300)
    HIGH = (500, 500)
    EPIC = (1000, 1000)
    
    @property
    def min_width(self) -> int:
        return self.value[0]
    
    @property
    def min_height(self) -> int:
        return self.value[1]
    
    @classmethod
    def from_string(cls, s: str) -> "ImageQuality":
        """Convert string to ImageQuality enum."""
        mapping = {
            "low": cls.LOW,
            "medium": cls.MEDIUM,
            "mid": cls.MEDIUM,
            "middle": cls.MEDIUM,
            "high": cls.HIGH,
            "epic": cls.EPIC,
        }
        key = s.lower().strip()
        if key not in mapping:
            valid = ", ".join(mapping.keys())
            raise ValueError(f"Invalid quality '{s}'. Valid options: {valid}")
        return mapping[key]


@dataclass
class ImageInfo:
    """Information about an extracted image."""
    
    xref: int  # PDF internal reference number
    page: int  # 0-based page index
    width: int  # Image width in pixels
    height: int  # Image height in pixels
    bpc: int  # Bits per component (color depth)
    colorspace: str  # e.g., "DeviceRGB", "DeviceGray"
    image_format: str  # e.g., "png", "jpeg"
    size_bytes: int  # Image data size
    file_path: Optional[str] = None  # Path if saved to disk
    
    @property
    def resolution(self) -> int:
        """Total pixel count (width * height)."""
        return self.width * self.height
    
    @property
    def is_color(self) -> bool:
        """Whether the image is in color."""
        return "RGB" in self.colorspace or "CMYK" in self.colorspace


@dataclass
class ImageMetadata:
    """
    Metadata about an extracted image including position information.
    
    Used for generating manifest JSON files.
    """
    
    filename: str  # Output filename (e.g., "paper_fig1.png")
    page: int  # 0-based page index
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1) in page coordinates
    position: str  # Human-readable position (e.g., "top", "center", "bottom-left")
    description: str  # Full description (e.g., "Figure at the top of page 3")
    width: int  # Image width in pixels
    height: int  # Image height in pixels
    xref: int  # PDF internal reference
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "filename": self.filename,
            "page": self.page + 1,  # 1-based for user-friendly output
            "description": self.description,
        }
    
    def to_full_dict(self) -> Dict[str, Any]:
        """Convert to dictionary with full details."""
        return {
            "filename": self.filename,
            "page": self.page + 1,
            "position": self.position,
            "description": self.description,
            "bbox": self.bbox,
            "width": self.width,
            "height": self.height,
            "xref": self.xref,
        }


@dataclass
class ConversionOptions:
    """Options for PDF to Markdown conversion."""
    
    # Page selection
    pages: Optional[List[int]] = None  # None = all pages, list of 0-based indices
    
    # Image handling
    write_images: bool = False  # Save images to disk
    embed_images: bool = False  # Embed images as base64 in markdown
    image_path: str = ""  # Directory to save images (if write_images=True)
    image_format: str = "png"  # Image format: png, jpg, etc.
    image_dpi: int = 150  # DPI for image extraction
    
    # Output format
    page_chunks: bool = False  # Return list of dicts per page instead of single string
    page_separators: bool = False  # Add page separator comments
    include_header: bool = True  # Include document header info
    include_footer: bool = True  # Include document footer info
    ignore_code: bool = False  # Skip code block formatting
    
    # OCR options
    use_ocr: bool = False  # Enable OCR for scanned PDFs
    force_ocr: bool = False  # Force OCR even if text exists
    ocr_language: str = "eng"  # OCR language (Tesseract language code)
    ocr_dpi: int = 300  # DPI for OCR processing
    
    # Progress
    show_progress: bool = False  # Show progress during conversion


@dataclass
class ConversionResult:
    """Result of a PDF to Markdown conversion."""
    
    success: bool
    markdown: Optional[str] = None  # Full markdown text (if page_chunks=False)
    chunks: Optional[List[Dict[str, Any]]] = None  # Per-page chunks (if page_chunks=True)
    metadata: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None
    
    @property
    def page_count(self) -> int:
        """Number of pages processed."""
        if self.chunks:
            return len(self.chunks)
        return self.metadata.get("page_count", 0)


class PDFConverter:
    """
    High-level API for converting PDF documents to Markdown.
    
    Uses PyMuPDF4LLM for intelligent structure detection including:
    - Headers, paragraphs, and lists
    - Tables in Markdown format
    - Multi-column layout handling
    - Image extraction
    
    Example:
        converter = PDFConverter()
        result = converter.convert("paper.pdf")
        
        if result.success:
            print(result.markdown)
        
        # Or with options:
        result = converter.convert(
            "paper.pdf",
            options=ConversionOptions(
                pages=[0, 1, 2],
                write_images=True,
                image_path="./images",
            )
        )
    """
    
    def __init__(self, default_options: Optional[ConversionOptions] = None):
        """
        Initialize the PDF converter.
        
        Args:
            default_options: Default conversion options to use.
        """
        self.default_options = default_options or ConversionOptions()
    
    def convert(
        self,
        pdf_path: Union[str, Path],
        options: Optional[ConversionOptions] = None,
    ) -> ConversionResult:
        """
        Convert a PDF document to Markdown.
        
        Args:
            pdf_path: Path to the PDF file.
            options: Conversion options. If None, uses default options.
        
        Returns:
            ConversionResult with markdown text or chunks.
        """
        opts = options or self.default_options
        pdf_path = Path(pdf_path)
        
        if not pdf_path.exists():
            return ConversionResult(
                success=False,
                error=f"File not found: {pdf_path}",
            )
        
        try:
            # Get document metadata first
            doc = pymupdf.open(str(pdf_path))
            metadata = {
                "page_count": doc.page_count,
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "file_path": str(pdf_path),
                "file_name": pdf_path.name,
            }
            doc.close()
            
            # Convert to markdown
            result = pymupdf4llm.to_markdown(
                str(pdf_path),
                pages=opts.pages,
                write_images=opts.write_images,
                embed_images=opts.embed_images,
                image_path=opts.image_path,
                image_format=opts.image_format,
                dpi=opts.image_dpi,
                page_chunks=opts.page_chunks,
                page_separators=opts.page_separators,
                header=opts.include_header,
                footer=opts.include_footer,
                ignore_code=opts.ignore_code,
                use_ocr=opts.use_ocr,
                force_ocr=opts.force_ocr,
                ocr_language=opts.ocr_language,
                ocr_dpi=opts.ocr_dpi,
                show_progress=opts.show_progress,
            )
            
            if opts.page_chunks:
                return ConversionResult(
                    success=True,
                    chunks=result,
                    metadata=metadata,
                )
            else:
                return ConversionResult(
                    success=True,
                    markdown=result,
                    metadata=metadata,
                )
        
        except Exception as e:
            return ConversionResult(
                success=False,
                error=str(e),
            )
    
    def convert_pages(
        self,
        pdf_path: Union[str, Path],
        pages: List[int],
        **kwargs,
    ) -> ConversionResult:
        """
        Convert specific pages of a PDF to Markdown.
        
        Args:
            pdf_path: Path to the PDF file.
            pages: List of 0-based page indices to convert.
            **kwargs: Additional options passed to ConversionOptions.
        
        Returns:
            ConversionResult with markdown text.
        """
        options = ConversionOptions(pages=pages, **kwargs)
        return self.convert(pdf_path, options)
    
    def convert_to_chunks(
        self,
        pdf_path: Union[str, Path],
        **kwargs,
    ) -> ConversionResult:
        """
        Convert a PDF to per-page Markdown chunks.
        
        Useful for RAG applications where you need to process pages individually.
        
        Args:
            pdf_path: Path to the PDF file.
            **kwargs: Additional options passed to ConversionOptions.
        
        Returns:
            ConversionResult with chunks (list of dicts per page).
        """
        options = ConversionOptions(page_chunks=True, **kwargs)
        return self.convert(pdf_path, options)
    
    def extract_text(
        self,
        pdf_path: Union[str, Path],
        pages: Optional[List[int]] = None,
    ) -> str:
        """
        Extract plain text from a PDF (without Markdown formatting).
        
        Args:
            pdf_path: Path to the PDF file.
            pages: List of 0-based page indices. None = all pages.
        
        Returns:
            Plain text content of the PDF.
        """
        pdf_path = Path(pdf_path)
        doc = pymupdf.open(str(pdf_path))
        
        try:
            text_parts = []
            page_indices = pages if pages else range(doc.page_count)
            
            for page_idx in page_indices:
                if 0 <= page_idx < doc.page_count:
                    page = doc[page_idx]
                    text_parts.append(page.get_text())
            
            return "\n\n".join(text_parts)
        finally:
            doc.close()
    
    def get_metadata(self, pdf_path: Union[str, Path]) -> Dict[str, Any]:
        """
        Get metadata from a PDF document.
        
        Args:
            pdf_path: Path to the PDF file.
        
        Returns:
            Dictionary with document metadata.
        """
        pdf_path = Path(pdf_path)
        doc = pymupdf.open(str(pdf_path))
        
        try:
            return {
                "page_count": doc.page_count,
                "title": doc.metadata.get("title", ""),
                "author": doc.metadata.get("author", ""),
                "subject": doc.metadata.get("subject", ""),
                "keywords": doc.metadata.get("keywords", ""),
                "creator": doc.metadata.get("creator", ""),
                "producer": doc.metadata.get("producer", ""),
                "creation_date": doc.metadata.get("creationDate", ""),
                "modification_date": doc.metadata.get("modDate", ""),
                "format": doc.metadata.get("format", ""),
                "encryption": doc.metadata.get("encryption", ""),
                "file_path": str(pdf_path),
                "file_name": pdf_path.name,
                "file_size": pdf_path.stat().st_size,
            }
        finally:
            doc.close()
    
    def extract_images(
        self,
        pdf_path: Union[str, Path],
        output_dir: Union[str, Path],
        *,
        pages: Optional[List[int]] = None,
        quality: Union[str, ImageQuality] = "high",
        min_resolution: int = 10000,
        image_format: str = "png",
        deduplicate: bool = True,
        name_prefix: str = "paper",
    ) -> List[ImageInfo]:
        """
        Extract high-quality images from a PDF document.
        
        Filters out small icons, decorative elements, and low-resolution images.
        Only extracts images meeting the quality thresholds.
        
        Args:
            pdf_path: Path to the PDF file.
            output_dir: Directory to save extracted images.
            pages: List of 0-based page indices. None = all pages.
            quality: Quality level filter. Can be:
                     - "low" (100x100): Includes small icons and thumbnails
                     - "medium"/"mid" (300x300): Moderate quality images
                     - "high" (500x500): Good quality figures (default)
                     - "epic" (1000x1000): Publication-quality, large figures only
                     Or an ImageQuality enum value.
            min_resolution: Minimum total pixels (width * height, default: 10000).
            image_format: Output format: "png", "jpeg", "original" (default: "png").
                         "original" keeps the source format.
            deduplicate: Skip duplicate images by xref (default: True).
            name_prefix: Prefix for output filenames (default: "paper").
                        Use Zotero attachment key for traceability (e.g., "SNX599P2").
                        Output format: {prefix}_fig{num}.{ext}
        
        Returns:
            List of ImageInfo objects for successfully extracted images.
        
        Example:
            converter = PDFConverter()
            
            # Default naming: paper_fig1.png, paper_fig2.png, ...
            images = converter.extract_images("paper.pdf", "./figures")
            
            # Custom prefix (recommended: use Zotero attachment key)
            images = converter.extract_images(
                "paper.pdf",
                "./figures",
                quality="high",
                name_prefix="SNX599P2",  # -> SNX599P2_fig1.png, SNX599P2_fig2.png, ...
            )
            for img in images:
                print(f"Page {img.page}: {img.width}x{img.height} -> {img.file_path}")
        """
        # Parse quality parameter
        if isinstance(quality, str):
            q = ImageQuality.from_string(quality)
        else:
            q = quality
        min_width = q.min_width
        min_height = q.min_height
        
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Use provided prefix for filenames
        fig_counter = 0
        
        doc = pymupdf.open(str(pdf_path))
        extracted_images: List[ImageInfo] = []
        seen_xrefs: set = set()
        
        try:
            page_indices = pages if pages else range(doc.page_count)
            
            for page_idx in page_indices:
                if not (0 <= page_idx < doc.page_count):
                    continue
                
                page = doc[page_idx]
                image_list = page.get_images(full=True)
                
                for img_info in image_list:
                    xref = img_info[0]
                    
                    # Skip duplicates if enabled
                    if deduplicate and xref in seen_xrefs:
                        continue
                    seen_xrefs.add(xref)
                    
                    try:
                        # Extract image data
                        base_image = doc.extract_image(xref)
                        if not base_image:
                            continue
                        
                        width = base_image["width"]
                        height = base_image["height"]
                        bpc = base_image.get("bpc", 8)
                        colorspace_name = base_image.get("colorspace", 1)
                        # Convert colorspace number to name if needed
                        if isinstance(colorspace_name, int):
                            colorspace_map = {1: "DeviceGray", 3: "DeviceRGB", 4: "DeviceCMYK"}
                            colorspace_name = colorspace_map.get(colorspace_name, f"CS{colorspace_name}")
                        
                        image_data = base_image["image"]
                        ext = base_image["ext"]  # Original format extension
                        
                        # Apply quality filters
                        if width < min_width or height < min_height:
                            continue
                        if width * height < min_resolution:
                            continue
                        
                        # Determine output format
                        if image_format == "original":
                            out_ext = ext
                        else:
                            out_ext = image_format
                        
                        # Generate simple filename: {prefix}_fig{num}.{ext}
                        fig_counter += 1
                        filename = f"{name_prefix}_fig{fig_counter}.{out_ext}"
                        out_path = output_dir / filename
                        
                        # Save image
                        if image_format == "original" or ext == image_format:
                            # Write directly
                            out_path.write_bytes(image_data)
                        else:
                            # Convert format using pixmap
                            pix = pymupdf.Pixmap(image_data)
                            if pix.alpha:  # Remove alpha for JPEG
                                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                            if out_ext == "png":
                                pix.save(str(out_path))
                            elif out_ext in ("jpg", "jpeg"):
                                pix.save(str(out_path), jpg_quality=95)
                            else:
                                pix.save(str(out_path))
                        
                        extracted_images.append(ImageInfo(
                            xref=xref,
                            page=page_idx,
                            width=width,
                            height=height,
                            bpc=bpc,
                            colorspace=colorspace_name,
                            image_format=out_ext,
                            size_bytes=len(image_data),
                            file_path=str(out_path),
                        ))
                    
                    except Exception:
                        # Skip problematic images
                        continue
            
            return extracted_images
        
        finally:
            doc.close()
    
    def list_images(
        self,
        pdf_path: Union[str, Path],
        pages: Optional[List[int]] = None,
    ) -> List[ImageInfo]:
        """
        List all images in a PDF without extracting them.
        
        Useful for analyzing image content before extraction.
        
        Args:
            pdf_path: Path to the PDF file.
            pages: List of 0-based page indices. None = all pages.
        
        Returns:
            List of ImageInfo objects (without file_path set).
        """
        pdf_path = Path(pdf_path)
        doc = pymupdf.open(str(pdf_path))
        images: List[ImageInfo] = []
        seen_xrefs: set = set()
        
        try:
            page_indices = pages if pages else range(doc.page_count)
            
            for page_idx in page_indices:
                if not (0 <= page_idx < doc.page_count):
                    continue
                
                page = doc[page_idx]
                image_list = page.get_images(full=True)
                
                for img_info in image_list:
                    xref = img_info[0]
                    
                    if xref in seen_xrefs:
                        continue
                    seen_xrefs.add(xref)
                    
                    try:
                        base_image = doc.extract_image(xref)
                        if not base_image:
                            continue
                        
                        width = base_image["width"]
                        height = base_image["height"]
                        bpc = base_image.get("bpc", 8)
                        colorspace_name = base_image.get("colorspace", 1)
                        if isinstance(colorspace_name, int):
                            colorspace_map = {1: "DeviceGray", 3: "DeviceRGB", 4: "DeviceCMYK"}
                            colorspace_name = colorspace_map.get(colorspace_name, f"CS{colorspace_name}")
                        
                        images.append(ImageInfo(
                            xref=xref,
                            page=page_idx,
                            width=width,
                            height=height,
                            bpc=bpc,
                            colorspace=colorspace_name,
                            image_format=base_image["ext"],
                            size_bytes=len(base_image["image"]),
                        ))
                    except Exception:
                        continue
            
            return images
        
        finally:
            doc.close()
    
    @staticmethod
    def _get_position_description(
        bbox: Tuple[float, float, float, float],
        page_height: float,
        page_width: float,
    ) -> Tuple[str, str]:
        """
        Determine position description from bounding box.
        
        Args:
            bbox: (x0, y0, x1, y1) image bounding box in page coordinates.
            page_height: Total page height.
            page_width: Total page width.
        
        Returns:
            Tuple of (position_short, description_phrase):
            - position_short: e.g., "top", "center", "bottom-left"
            - description_phrase: e.g., "at the top of"
        """
        # Calculate center point of the image
        x0, y0, x1, y1 = bbox
        center_x = (x0 + x1) / 2
        center_y = (y0 + y1) / 2
        
        # Determine vertical position (PDF coordinates: y=0 at top)
        y_ratio = center_y / page_height if page_height > 0 else 0.5
        if y_ratio < 0.33:
            v_pos = "top"
            v_phrase = "at the top of"
        elif y_ratio < 0.66:
            v_pos = "center"
            v_phrase = "in the center of"
        else:
            v_pos = "bottom"
            v_phrase = "at the bottom of"
        
        # Determine horizontal position
        x_ratio = center_x / page_width if page_width > 0 else 0.5
        if x_ratio < 0.33:
            h_pos = "left"
        elif x_ratio > 0.66:
            h_pos = "right"
        else:
            h_pos = ""  # Center, don't add horizontal qualifier
        
        # Combine positions
        if h_pos:
            position = f"{v_pos}-{h_pos}"
            description = f"{v_phrase.replace('of', '')}({h_pos}) of"
        else:
            position = v_pos
            description = v_phrase
        
        return position, description
    
    def extract_images_with_metadata(
        self,
        pdf_path: Union[str, Path],
        output_dir: Union[str, Path],
        *,
        pages: Optional[List[int]] = None,
        quality: Union[str, ImageQuality] = "high",
        min_resolution: int = 10000,
        image_format: str = "png",
        deduplicate: bool = True,
        name_prefix: str = "paper",
    ) -> List[ImageMetadata]:
        """
        Extract images with position metadata for manifest generation.
        
        Similar to extract_images(), but returns ImageMetadata objects
        with bounding box and position information.
        
        Args:
            pdf_path: Path to the PDF file.
            output_dir: Directory to save extracted images.
            pages: List of 0-based page indices. None = all pages.
            quality: Quality level filter ("low", "medium", "high", "epic").
            min_resolution: Minimum total pixels (width * height).
            image_format: Output format: "png", "jpeg", "original".
            deduplicate: Skip duplicate images by xref.
            name_prefix: Prefix for output filenames.
        
        Returns:
            List of ImageMetadata objects with position information.
        
        Example:
            converter = PDFConverter()
            metadata = converter.extract_images_with_metadata(
                "paper.pdf",
                "./figures",
                name_prefix="SNX599P2",
            )
            
            # Save manifest
            converter.save_image_manifest(metadata, "./figures/manifest.json")
        """
        # Parse quality parameter
        if isinstance(quality, str):
            q = ImageQuality.from_string(quality)
        else:
            q = quality
        min_width = q.min_width
        min_height = q.min_height
        
        pdf_path = Path(pdf_path)
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        
        fig_counter = 0
        doc = pymupdf.open(str(pdf_path))
        metadata_list: List[ImageMetadata] = []
        seen_xrefs: set = set()
        
        try:
            page_indices = pages if pages else range(doc.page_count)
            
            for page_idx in page_indices:
                if not (0 <= page_idx < doc.page_count):
                    continue
                
                page = doc[page_idx]
                page_rect = page.rect
                page_width = page_rect.width
                page_height = page_rect.height
                image_list = page.get_images(full=True)
                
                for img_info in image_list:
                    xref = img_info[0]
                    
                    if deduplicate and xref in seen_xrefs:
                        continue
                    seen_xrefs.add(xref)
                    
                    try:
                        base_image = doc.extract_image(xref)
                        if not base_image:
                            continue
                        
                        width = base_image["width"]
                        height = base_image["height"]
                        image_data = base_image["image"]
                        ext = base_image["ext"]
                        
                        # Apply quality filters
                        if width < min_width or height < min_height:
                            continue
                        if width * height < min_resolution:
                            continue
                        
                        # Get bounding box on page
                        try:
                            bbox_result = page.get_image_bbox(img_info)
                            if bbox_result.is_infinite or bbox_result.is_empty:
                                # Image not displayed on page, skip
                                continue
                            bbox = (bbox_result.x0, bbox_result.y0, 
                                    bbox_result.x1, bbox_result.y1)
                        except Exception:
                            # Fallback: use (0, 0, page_width, page_height)
                            bbox = (0, 0, page_width, page_height)
                        
                        # Get position description
                        position, desc_phrase = self._get_position_description(
                            bbox, page_height, page_width
                        )
                        
                        # Determine output format
                        if image_format == "original":
                            out_ext = ext
                        else:
                            out_ext = image_format
                        
                        # Generate filename
                        fig_counter += 1
                        filename = f"{name_prefix}_fig{fig_counter}.{out_ext}"
                        out_path = output_dir / filename
                        
                        # Save image
                        if image_format == "original" or ext == image_format:
                            out_path.write_bytes(image_data)
                        else:
                            pix = pymupdf.Pixmap(image_data)
                            if pix.alpha:
                                pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                            if out_ext == "png":
                                pix.save(str(out_path))
                            elif out_ext in ("jpg", "jpeg"):
                                pix.save(str(out_path), jpg_quality=95)
                            else:
                                pix.save(str(out_path))
                        
                        # Generate description
                        description = f"Figure {desc_phrase} page {page_idx + 1}"
                        
                        metadata_list.append(ImageMetadata(
                            filename=filename,
                            page=page_idx,
                            bbox=bbox,
                            position=position,
                            description=description,
                            width=width,
                            height=height,
                            xref=xref,
                        ))
                    
                    except Exception:
                        continue
            
            return metadata_list
        
        finally:
            doc.close()
    
    def save_image_manifest(
        self,
        metadata: List[ImageMetadata],
        output_path: Union[str, Path],
        *,
        include_full_details: bool = False,
        indent: int = 2,
    ) -> None:
        """
        Save image metadata to a JSON manifest file.
        
        Args:
            metadata: List of ImageMetadata objects.
            output_path: Path for the output JSON file.
            include_full_details: If True, include bbox and pixel dimensions.
                                  If False, only filename, page, description.
            indent: JSON indentation level (default: 2).
        
        Example:
            converter = PDFConverter()
            metadata = converter.extract_images_with_metadata("paper.pdf", "./figures")
            
            # Simple manifest
            converter.save_image_manifest(metadata, "./figures/manifest.json")
            # Output: [{"filename": "paper_fig1.png", "page": 1, "description": "Figure at the top of page 1"}, ...]
            
            # Full details
            converter.save_image_manifest(metadata, "./figures/manifest_full.json", include_full_details=True)
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if include_full_details:
            data = [m.to_full_dict() for m in metadata]
        else:
            data = [m.to_dict() for m in metadata]
        
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=indent, ensure_ascii=False)


def markdown_to_html(md_content: str, strip_images: bool = True) -> str:
    """
    Convert Markdown content to HTML, optionally stripping image references.
    
    Zotero notes only support HTML format and cannot display embedded images.
    This function converts Markdown to HTML and can remove image syntax before
    conversion to produce clean note content.
    
    Args:
        md_content: Raw markdown string.
        strip_images: If True, removes all ![alt](path) image references
                      before conversion. Defaults to True.
    
    Returns:
        HTML string suitable for Zotero notes.
    
    Example:
        md = "# Title\n\n![figure](fig.png)\n\nSome text."
        html = markdown_to_html(md, strip_images=True)
        # Returns: "<h1>Title</h1>\n<p>Some text.</p>"
    """
    import re
    import markdown as md_lib
    
    content = md_content
    
    if strip_images:
        # Remove markdown image syntax: ![alt text](path)
        # Also handles optional title: ![alt](path "title")
        content = re.sub(r'!\[[^\]]*\]\([^)]+\)', '', content)
        # Clean up empty lines that may result from image removal
        content = re.sub(r'\n{3,}', '\n\n', content)
    
    # Convert to HTML with common extensions
    html = md_lib.markdown(
        content,
        extensions=['tables', 'fenced_code', 'toc'],
    )
    
    return html
