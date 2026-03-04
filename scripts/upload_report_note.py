"""
Upload a Markdown report as a Zotero note.

This script converts a Markdown report to HTML (stripping image references)
and attaches it as a note to a specified Zotero item.

Usage:
    python scripts/upload_report_note.py --report path/to/report.md --zotero-key ABC12345
    
    # With custom tags
    python scripts/upload_report_note.py --report path/to/report.md --zotero-key ABC12345 --tags summary,auto-generated
"""

from __future__ import annotations

import argparse
from pathlib import Path

from stable_jarvis_dev import markdown_to_html, ZoteroClient


def upload_report_as_note(
    report_path: Path,
    zotero_item_key: str,
    tags: list[str] | None = None,
) -> str:
    """
    Upload a Markdown report as a Zotero note.
    
    Args:
        report_path: Path to the Markdown report file.
        zotero_item_key: The Zotero item key to attach the note to.
            Can be either the main item key (e.g., journal article) or
            an attachment key (e.g., PDF). If an attachment key is provided,
            the note will be attached to its parent item.
        tags: Optional list of tags to apply to the note.
    
    Returns:
        The Zotero item key of the created note.
    
    Raises:
        FileNotFoundError: If the report file doesn't exist.
        RuntimeError: If the Zotero API call fails.
    """
    report_path = Path(report_path)
    
    if not report_path.exists():
        raise FileNotFoundError(f"Report file not found: {report_path}")
    
    # Read the markdown content
    md_content = report_path.read_text(encoding="utf-8")
    
    # Convert to HTML, stripping images (Zotero notes don't support embedded images)
    html_content = markdown_to_html(md_content, strip_images=True)
    
    # Create the note via Zotero API
    client = ZoteroClient()
    
    # Resolve attachment keys to their parent items
    # Notes should be attached to the main item (e.g., journalArticle), not attachments
    item = client._zot.item(zotero_item_key)
    item_type = item.get("data", {}).get("itemType", "")
    
    if item_type == "attachment":
        parent_key = item.get("data", {}).get("parentItem")
        if parent_key:
            print(f"Note: {zotero_item_key} is an attachment, attaching note to parent {parent_key}")
            zotero_item_key = parent_key
        else:
            raise RuntimeError(f"Attachment {zotero_item_key} has no parent item")
    
    note_key = client.create_note(
        parent_key=zotero_item_key,
        html_content=html_content,
        tags=tags,
    )
    
    return note_key


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Upload a Markdown report as a Zotero note.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--report",
        type=Path,
        required=True,
        help="Path to the Markdown report file",
    )
    parser.add_argument(
        "--zotero-key",
        type=str,
        required=True,
        help="Zotero item key to attach the note to (the parent paper item)",
    )
    parser.add_argument(
        "--tags",
        type=str,
        default=None,
        help="Comma-separated list of tags to apply to the note (e.g., 'summary,auto-generated')",
    )
    
    args = parser.parse_args()
    
    tags = [t.strip() for t in args.tags.split(",")] if args.tags else None
    
    try:
        note_key = upload_report_as_note(
            report_path=args.report,
            zotero_item_key=args.zotero_key,
            tags=tags,
        )
        print(f"Successfully created note: {note_key}")
    except FileNotFoundError as e:
        print(f"Error: {e}")
        exit(1)
    except RuntimeError as e:
        print(f"Zotero API error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
