"""
High-level annotation API.
Main entry point for programmatic PDF annotation via Zotero.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple

from .config import ZoteroConfig, get_default_config
from .coordinates import CoordinateExtractor, TextMatch
from .zotero_client import AnnotationPayload, ZoteroClient

logger = logging.getLogger(__name__)


@dataclass
class AnnotationResult:
    """Result of an annotation operation."""
    success: bool
    annotation_key: Optional[str] = None
    match: Optional[TextMatch] = None
    error: Optional[str] = None
    shortened_text: Optional[str] = None  # If auto-shortening was used
    original_text: Optional[str] = None  # Original target text before shortening


def _shorten_text(text: str, keep_ratio: float = 0.8) -> str:
    """
    Shorten text by keeping a percentage of words from the start.
    
    Args:
        text: Original text.
        keep_ratio: Fraction of words to keep (0.0 to 1.0).
    
    Returns:
        Shortened text with fewer words.
    """
    words = text.split()
    keep_count = max(3, int(len(words) * keep_ratio))  # Keep at least 3 words
    if keep_count >= len(words):
        return text
    return " ".join(words[:keep_count])


class ZoteroAnnotator:
    """
    High-level API for adding annotations to PDFs in Zotero.
    
    This class orchestrates coordinate extraction from local PDF files
    and annotation injection via the Zotero Web API.
    
    Example:
        annotator = ZoteroAnnotator()
        result = annotator.highlight(
            pdf_path="path/to/paper.pdf",
            attachment_key="ABC12345",
            target_text="important sentence to highlight",
            comment="This is a key finding",
            color="#ff6666",
        )
        if result.success:
            print(f"Created annotation: {result.annotation_key}")
    """
    
    def __init__(
        self,
        config: Optional[ZoteroConfig] = None,
        flip_y: bool = True,
    ):
        """
        Initialize the annotator.
        
        Args:
            config: ZoteroConfig instance. If None, loads from default location.
            flip_y: Whether to flip Y coordinates (PyMuPDF top-left → PDF bottom-left).
                    Default True for Zotero 7+.
        """
        self.config = config or get_default_config()
        self.extractor = CoordinateExtractor(flip_y=flip_y)
        self.client = ZoteroClient(config=self.config)
    
    def highlight(
        self,
        pdf_path: str | Path,
        attachment_key: str,
        target_text: str,
        page_index: int = 0,
        comment: str = "",
        color: str = "#ffd400",
    ) -> AnnotationResult:
        """
        Add a highlight annotation to a PDF.
        
        Args:
            pdf_path: Local path to the PDF file.
            attachment_key: Zotero item key of the PDF attachment.
            target_text: Text to highlight.
            page_index: 0-based page number (default: 0).
            comment: Optional annotation comment.
            color: Highlight color in hex format (default: yellow #ffd400).
        
        Returns:
            AnnotationResult with success status and annotation key.
        """
        return self._annotate(
            pdf_path=pdf_path,
            attachment_key=attachment_key,
            target_text=target_text,
            annotation_type="highlight",
            page_index=page_index,
            comment=comment,
            color=color,
        )
    
    def underline(
        self,
        pdf_path: str | Path,
        attachment_key: str,
        target_text: str,
        page_index: int = 0,
        comment: str = "",
        color: str = "#2ea8e5",
    ) -> AnnotationResult:
        """
        Add an underline annotation to a PDF.
        
        Args:
            pdf_path: Local path to the PDF file.
            attachment_key: Zotero item key of the PDF attachment.
            target_text: Text to underline.
            page_index: 0-based page number (default: 0).
            comment: Optional annotation comment.
            color: Underline color in hex format (default: blue #2ea8e5).
        
        Returns:
            AnnotationResult with success status and annotation key.
        """
        return self._annotate(
            pdf_path=pdf_path,
            attachment_key=attachment_key,
            target_text=target_text,
            annotation_type="underline",
            page_index=page_index,
            comment=comment,
            color=color,
        )
    
    def _annotate(
        self,
        pdf_path: str | Path,
        attachment_key: str,
        target_text: str,
        annotation_type: str,
        page_index: int = 0,
        comment: str = "",
        color: str = "#ffd400",
        auto_shorten: bool = True,
        max_shorten_attempts: int = 3,
    ) -> AnnotationResult:
        """
        Internal method to create an annotation with auto-shortening retry.
        
        Args:
            pdf_path: Local path to the PDF file.
            attachment_key: Zotero item key of the PDF attachment.
            target_text: Text to annotate.
            annotation_type: Type of annotation ("highlight", "underline", etc.).
            page_index: 0-based page number.
            comment: Optional annotation comment.
            color: Annotation color in hex format.
            auto_shorten: If True, automatically retry with shorter text on failure.
            max_shorten_attempts: Maximum number of shortening attempts.
        
        Returns:
            AnnotationResult with success status and details.
        """
        original_text = target_text
        attempts: List[Tuple[str, str]] = []  # (text_tried, error)
        
        # Try with progressively shorter text
        text_variants = [target_text]
        if auto_shorten and len(target_text.split()) > 5:
            text_variants.extend([
                _shorten_text(target_text, 0.8),  # 80% of words
                _shorten_text(target_text, 0.6),  # 60% of words
                _shorten_text(target_text, 0.4),  # 40% of words
            ])
            # Remove duplicates while preserving order
            seen = set()
            unique_variants = []
            for v in text_variants:
                if v not in seen:
                    seen.add(v)
                    unique_variants.append(v)
            text_variants = unique_variants[:max_shorten_attempts + 1]
        
        last_error: Optional[str] = None
        
        for attempt_idx, current_text in enumerate(text_variants):
            try:
                # Step 1: Extract coordinates
                match = self.extractor.extract(
                    pdf_path=pdf_path,
                    target_text=current_text,
                    page_index=page_index,
                )
                
                # Step 2: Build payload
                payload = AnnotationPayload(
                    parent_item=attachment_key,
                    annotation_type=annotation_type,
                    page_index=page_index,
                    rects=match.rects,
                    text=current_text,
                    comment=comment,
                    color=color,
                )
                
                # Step 3: Upload to Zotero
                annotation_key = self.client.create_annotation(payload)
                
                # Determine if we used a shortened version
                used_shortened = current_text != original_text
                
                if used_shortened:
                    logger.info(
                        f"Text matching succeeded with shortened text "
                        f"(attempt {attempt_idx + 1}): '{current_text[:50]}...'"
                    )
                
                return AnnotationResult(
                    success=True,
                    annotation_key=annotation_key,
                    match=match,
                    shortened_text=current_text if used_shortened else None,
                    original_text=original_text if used_shortened else None,
                )
            
            except ValueError as e:
                # Text not found - try shorter version
                last_error = str(e)
                attempts.append((current_text, last_error))
                logger.debug(f"Attempt {attempt_idx + 1} failed: {e}")
                continue
            
            except Exception as e:
                # Other errors - don't retry
                return AnnotationResult(
                    success=False,
                    error=str(e),
                    original_text=original_text,
                )
        
        # All attempts failed
        error_msg = f"Text matching failed after {len(attempts)} attempts. "
        if len(attempts) > 1:
            error_msg += "Tried shortened variants but none matched. "
        error_msg += f"Last error: {last_error}"
        
        return AnnotationResult(
            success=False,
            error=error_msg,
            original_text=original_text,
        )


def annotate(
    pdf_path: str | Path,
    attachment_key: str,
    target_text: str,
    annotation_type: str = "highlight",
    page_index: int = 0,
    comment: str = "",
    color: str = "#ffd400",
    config: Optional[ZoteroConfig] = None,
) -> AnnotationResult:
    """
    Convenience function to add an annotation with a single call.
    
    Args:
        pdf_path: Local path to the PDF file.
        attachment_key: Zotero item key of the PDF attachment.
        target_text: Text to annotate.
        annotation_type: Type of annotation ("highlight", "underline").
        page_index: 0-based page number (default: 0).
        comment: Optional annotation comment.
        color: Annotation color in hex format.
        config: Optional ZoteroConfig (loads from default if None).
    
    Returns:
        AnnotationResult with success status and annotation key.
    
    Example:
        from stable_jarvis_dev.annotation import annotate
        
        result = annotate(
            pdf_path="paper.pdf",
            attachment_key="ABC12345",
            target_text="key finding",
            comment="Important!",
        )
    """
    annotator = ZoteroAnnotator(config=config)
    return annotator._annotate(
        pdf_path=pdf_path,
        attachment_key=attachment_key,
        target_text=target_text,
        annotation_type=annotation_type,
        page_index=page_index,
        comment=comment,
        color=color,
    )
