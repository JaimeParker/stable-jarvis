"""
Zotero API client for annotation injection.
Handles communication with Zotero Web API via pyzotero.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional

from pyzotero import zotero

from .config import ZoteroConfig, get_default_config
from .retry import RetryConfig, retry_with_backoff

logger = logging.getLogger(__name__)


def _log_retry(exc: Exception, attempt: int, delay: float) -> None:
    """Log retry attempts for debugging."""
    logger.warning(
        f"Zotero API call failed (attempt {attempt}), retrying in {delay:.1f}s: {exc}"
    )


# Default retry configuration for Zotero API calls
ZOTERO_RETRY_CONFIG = RetryConfig(
    max_retries=3,
    base_delay=1.0,
    max_delay=30.0,
    exponential_base=2.0,
    jitter=True,
)


@dataclass
class AnnotationPayload:
    """Data structure for a Zotero annotation."""
    parent_item: str  # PDF attachment key
    annotation_type: str  # "highlight", "underline", "note", "image"
    page_index: int
    rects: List[List[float]]  # [[x0, y0, x1, y1], ...]
    text: str = ""
    comment: str = ""
    color: str = "#ffd400"  # Default yellow
    
    def to_zotero_dict(self) -> Dict[str, Any]:
        """Convert to Zotero API format."""
        position_dict = {
            "pageIndex": self.page_index,
            "rects": self.rects,
        }
        
        # Build sortIndex: "PPPPP|YYYYYY|XXXXX"
        first_rect = self.rects[0] if self.rects else [0, 0, 0, 0]
        sort_index = f"{self.page_index:05d}|{int(first_rect[1]):06d}|{int(first_rect[0]):05d}"
        
        return {
            "itemType": "annotation",
            "parentItem": self.parent_item,
            "annotationType": self.annotation_type,
            "annotationText": self.text,
            "annotationComment": self.comment,
            "annotationColor": self.color.lower(),  # Zotero requires lowercase
            "annotationPosition": json.dumps(position_dict),
            "annotationSortIndex": sort_index,
        }


class ZoteroClient:
    """
    Client for interacting with Zotero Web API.
    
    Example:
        client = ZoteroClient()
        key = client.create_annotation(payload)
    """
    
    def __init__(self, config: Optional[ZoteroConfig] = None):
        """
        Initialize the Zotero client.
        
        Args:
            config: ZoteroConfig instance. If None, loads from default location.
        """
        self.config = config or get_default_config()
        self._zot = zotero.Zotero(
            self.config.library_id,
            self.config.library_type,
            self.config.api_key,
        )
    
    @retry_with_backoff(ZOTERO_RETRY_CONFIG, on_retry=_log_retry)
    def create_annotation(self, payload: AnnotationPayload) -> str:
        """
        Create an annotation in Zotero.
        
        Args:
            payload: AnnotationPayload with annotation details.
        
        Returns:
            The Zotero item key of the created annotation.
        
        Raises:
            RuntimeError: If the API call fails.
        """
        annot_dict = payload.to_zotero_dict()
        resp = self._zot.create_items([annot_dict])
        
        if resp.get("failed"):
            error_msg = resp["failed"].get("0", {}).get("message", "Unknown error")
            raise RuntimeError(f"Zotero API error: {error_msg}")
        
        if resp.get("successful"):
            return list(resp["successful"].values())[0].get("key", "")
        
        raise RuntimeError(f"Unexpected API response: {resp}")
    
    @retry_with_backoff(ZOTERO_RETRY_CONFIG, on_retry=_log_retry)
    def get_attachment_info(self, attachment_key: str) -> Dict[str, Any]:
        """
        Get information about a PDF attachment.
        
        Args:
            attachment_key: The Zotero item key of the attachment.
        
        Returns:
            Dict with attachment metadata.
        """
        item = self._zot.item(attachment_key)
        return item.get("data", {})
    
    @retry_with_backoff(ZOTERO_RETRY_CONFIG, on_retry=_log_retry)
    def list_annotations(self, attachment_key: str) -> List[Dict[str, Any]]:
        """
        List all annotations under a PDF attachment.
        
        Args:
            attachment_key: The Zotero item key of the PDF attachment.
        
        Returns:
            List of annotation data dictionaries.
        """
        children = self._zot.children(attachment_key)
        return [
            child["data"]
            for child in children
            if child["data"].get("itemType") == "annotation"
        ]
    
    @retry_with_backoff(ZOTERO_RETRY_CONFIG, on_retry=_log_retry)
    def delete_annotation(self, annotation_key: str) -> bool:
        """
        Delete an annotation by its key.
        
        Args:
            annotation_key: The Zotero item key of the annotation.
        
        Returns:
            True if deletion was successful.
        """
        self._zot.delete_item(self._zot.item(annotation_key))
        return True
    
    @retry_with_backoff(ZOTERO_RETRY_CONFIG, on_retry=_log_retry)
    def create_note(
        self,
        parent_key: str,
        html_content: str,
        tags: Optional[List[str]] = None,
    ) -> str:
        """
        Create a note attached to a Zotero item.
        
        Notes in Zotero are stored as HTML. Use `markdown_to_html()` from
        the report_generator module to convert Markdown content.
        
        Args:
            parent_key: The Zotero item key of the parent item (e.g., a paper).
            html_content: HTML content for the note body.
            tags: Optional list of tag strings to apply to the note.
        
        Returns:
            The Zotero item key of the created note.
        
        Raises:
            RuntimeError: If the API call fails.
        
        Example:
            client = ZoteroClient()
            note_key = client.create_note(
                parent_key="ABC12345",
                html_content="<h1>Summary</h1><p>Key findings...</p>",
                tags=["summary", "auto-generated"],
            )
        """
        note_dict: Dict[str, Any] = {
            "itemType": "note",
            "note": html_content,
        }
        
        if tags:
            note_dict["tags"] = [{"tag": t} for t in tags]
        
        resp = self._zot.create_items([note_dict], parentid=parent_key)
        
        if resp.get("failed"):
            error_msg = resp["failed"].get("0", {}).get("message", "Unknown error")
            raise RuntimeError(f"Zotero API error: {error_msg}")
        
        if resp.get("successful"):
            return list(resp["successful"].values())[0].get("key", "")
        
        raise RuntimeError(f"Unexpected API response: {resp}")
