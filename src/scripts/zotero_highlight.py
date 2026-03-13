"""
CLI wrapper for Zotero highlight annotation.

Usage:
    python scripts/zotero_highlight.py <pdf_path> <attachment_key> <target_text> [options]
    python scripts/zotero_highlight.py --json <json_file>
    python scripts/zotero_highlight.py --info <pdf_path>

Examples:
    python scripts/zotero_highlight.py "D:\\path\\to\\paper.pdf" SNX599P2 "some text to highlight"
    python scripts/zotero_highlight.py "D:\\path\\to\\paper.pdf" SNX599P2 "target text" --page 0 --comment "My note" --color "#ff6666"
    python scripts/zotero_highlight.py --json annotation.json
    python scripts/zotero_highlight.py --info "D:\\path\\to\\paper.pdf"
"""

import argparse
import io
import json
import os
import re
import sys
from pathlib import Path

# Fix Windows console encoding for Unicode (Chinese characters)
if sys.platform == "win32":
    # Set environment variable to force UTF-8 mode
    os.environ.setdefault("PYTHONUTF8", "1")
    # Set stdout/stderr to UTF-8
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass  # Ignore if already wrapped

from stable_jarvis import ZoteroAnnotator, AnnotationResult
from stable_jarvis.annotation.coordinates import get_pdf_info, search_text_in_pdf


def try_fix_encoding(text: str) -> str:
    """
    Try to fix text that was incorrectly decoded from UTF-8 bytes as another encoding.
    This happens when Windows console passes UTF-8 text but Python decodes it as cp1252/gbk.
    """
    if not text:
        return text
    
    # Check if text looks like mojibake (garbled Unicode)
    # Common patterns: lots of rare CJK chars from wrong decoding
    suspicious_chars = set('绛碡瑗玙璖璆珟瑎鐎閸婢閺鐏缂閿閻娑閹')
    if any(c in suspicious_chars for c in text[:20]):
        # Try common encoding recovery patterns
        for wrong_encoding in ['cp1252', 'latin1', 'gbk', 'gb2312']:
            try:
                # Encode to bytes using wrong encoding, decode as UTF-8
                recovered = text.encode(wrong_encoding, errors='ignore').decode('utf-8', errors='ignore')
                if recovered and len(recovered) > 0:
                    # Check if recovery produced readable text
                    if not any(c in suspicious_chars for c in recovered[:20]):
                        return recovered
            except Exception:
                continue
    
    return text


def normalize_path(path_str: str) -> str:
    """
    Normalize a file path for cross-platform compatibility.
    
    Handles:
    - Windows backslashes (converts to forward slashes internally)
    - Double backslashes from JSON escaping
    - Path existence validation
    
    Args:
        path_str: The path string to normalize.
    
    Returns:
        Normalized path string.
    """
    if not path_str:
        return path_str
    
    # Handle double-escaped backslashes from JSON (\\\\  -> \\)
    path_str = path_str.replace("\\\\", "\\")
    
    # Convert to Path and back to string for normalization
    try:
        path = Path(path_str)
        # Return the path as-is (Path handles platform conversions)
        return str(path)
    except Exception:
        return path_str


def show_pdf_info(pdf_path: str) -> int:
    """
    Display information about a PDF file.
    
    Args:
        pdf_path: Path to the PDF file.
    
    Returns:
        Exit code (0 for success, 1 for error).
    """
    pdf_path = normalize_path(try_fix_encoding(pdf_path))
    
    # Check if file exists
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        print("\nTip: Make sure the path is correct. On Windows, you can use:")
        print("  - Forward slashes: D:/Documents/Zotero/storage/...")
        print("  - Double backslashes: D:\\\\Documents\\\\Zotero\\\\storage\\\\...")
        return 1
    
    try:
        info = get_pdf_info(pdf_path)
        
        print("=" * 60)
        print("PDF Information")
        print("=" * 60)
        print(f"File: {pdf_path}")
        print(f"Total Pages: {info.total_pages}")
        print(f"Has Cover Page: {'Yes' if info.has_cover else 'No'}")
        print()
        
        print("Page Dimensions (width x height in pt):")
        for i, (w, h) in enumerate(info.page_dimensions[:10]):  # Show first 10 pages
            label = info.page_labels[i] if i < len(info.page_labels) else str(i + 1)
            print(f"  Page {i} (label: {label}): {w:.0f} x {h:.0f}")
        
        if info.total_pages > 10:
            print(f"  ... and {info.total_pages - 10} more pages")
        
        print()
        print("Page Index Reference:")
        print("  - This tool uses 0-based page indexing")
        print("  - Page 0 = first page in PDF (may be a cover)")
        print("  - If your PDF viewer shows 'Page 1' for the first content page,")
        print("    you may need to use --page 1 (or higher) to skip front matter")
        
        if info.has_cover:
            print()
            print("  Note: This PDF appears to have a cover page (different dimensions).")
            print("  Consider using --page 1 to start from the first content page.")
        
        return 0
    
    except Exception as e:
        print(f"Error reading PDF: {e}")
        return 1


def search_pdf_text(pdf_path: str, query: str) -> int:
    """
    Search for text across all pages of a PDF.
    
    Args:
        pdf_path: Path to the PDF file.
        query: Text to search for.
    
    Returns:
        Exit code (0 for success, 1 for error).
    """
    pdf_path = normalize_path(try_fix_encoding(pdf_path))
    query = try_fix_encoding(query)
    
    # Check if file exists
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        return 1
    
    try:
        print("=" * 60)
        print("PDF Text Search")
        print("=" * 60)
        print(f"File: {pdf_path}")
        print(f"Query: {query!r}")
        print()
        
        results = search_text_in_pdf(pdf_path, query)
        
        if not results:
            print("No matches found.")
            print()
            print("Tips:")
            print("  1. Try shorter or different keywords")
            print("  2. Avoid math symbols (alpha, beta, omega, etc.)")
            print("  3. Use only plain English words")
            return 1
        
        print(f"Found {len(results)} potential match(es):")
        print()
        
        for r in results:
            confidence_str = f"{r['confidence']:.0%}" if r['confidence'] < 1.0 else "exact"
            print(f"  Page {r['page']} ({confidence_str} match, method: {r['method']})")
            # Clean up context for display
            context = r['context'].replace('\n', ' ').strip()
            if len(context) > 80:
                context = context[:80] + "..."
            print(f"    Context: {context}")
            print()
        
        print("Use the page number shown above for the --page argument.")
        return 0
    
    except Exception as e:
        print(f"Error searching PDF: {e}")
        return 1


def run_annotation(pdf_path: str, attachment_key: str, target_text: str, 
                   page: int, comment: str, color: str) -> int:
    """Run the annotation with given parameters."""
    # Normalize path and fix encoding issues
    pdf_path = normalize_path(try_fix_encoding(pdf_path))
    comment = try_fix_encoding(comment)
    
    # Validate file exists
    if not Path(pdf_path).exists():
        print(f"Error: PDF file not found: {pdf_path}")
        print("\nTip: Make sure the path is correct. On Windows, you can use:")
        print("  - Forward slashes: D:/Documents/Zotero/storage/...")
        print("  - Double backslashes in JSON: D:\\\\Documents\\\\...")
        return 1
    
    print(f"PDF: {pdf_path}")
    print(f"Attachment Key: {attachment_key}")
    print(f"Target Text: {target_text!r}")
    print(f"Page Index: {page}")
    print(f"Comment: {comment!r}")
    print(f"Color: {color}")
    print()

    # Create annotator instance
    annotator = ZoteroAnnotator()

    # Add highlight annotation
    print("Creating highlight annotation...")
    result: AnnotationResult = annotator.highlight(
        pdf_path=pdf_path,
        attachment_key=attachment_key,
        target_text=target_text,
        page_index=page,
        comment=comment,
        color=color,
    )

    if result.success:
        print(f"\nSuccess!")
        print(f"  Annotation Key: {result.annotation_key}")
        print(f"  Extraction Method: {result.match.method}")
        if result.match.method == "fuzzy":
            print(f"  Note: Fuzzy matching was used - verify the highlighted text is correct")
        elif result.match.method == "ultra_fuzzy":
            print(f"  Warning: Ultra-fuzzy matching was used (70% threshold)")
            print(f"           Please verify the highlighted text is correct!")
        
        # Show if text was auto-shortened
        if result.shortened_text:
            print(f"  Note: Text was auto-shortened for matching:")
            print(f"         Original: {result.original_text!r}")
            print(f"         Matched:  {result.shortened_text!r}")
        
        print(f"  Page Dimensions: {result.match.page_width:.0f} x {result.match.page_height:.0f} pt")
        print(f"  Rectangles: {len(result.match.rects)}")
        for i, rect in enumerate(result.match.rects):
            print(f"    [{i}] x0={rect[0]:.2f}, y0={rect[1]:.2f}, x1={rect[2]:.2f}, y1={rect[3]:.2f}")
        print("\nSync Zotero to see the highlight in the PDF reader.")
        return 0
    else:
        print(f"\nFailed: {result.error}")
        print("\nTroubleshooting tips:")
        print("  1. Try shortening the target_text (10-20 words work best)")
        print("  2. Verify the page index is correct (0-based)")
        print("  3. Avoid text with complex math symbols or Greek letters")
        print("  4. Use --info to inspect the PDF structure")
        print("  5. Check if the text spans multiple columns")
        return 1


def main():
    parser = argparse.ArgumentParser(
        description="Add highlight annotation to a PDF via Zotero Web API.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Direct command line (may have encoding issues with Chinese):
  python scripts/zotero_highlight.py "D:\\paper.pdf" ABC123 "important text"
  python scripts/zotero_highlight.py "D:\\paper.pdf" ABC123 "key finding" --page 1 --comment "Note"
  
  # Using JSON file (recommended for Unicode text):
  python scripts/zotero_highlight.py --json annotation.json
  
  # Get PDF information (page count, dimensions):
  python scripts/zotero_highlight.py --info "D:\\paper.pdf"
  
  # Search for text across all pages (pre-flight check):
  python scripts/zotero_highlight.py --search "D:\\paper.pdf" "gradient descent"
  
JSON file format:
{
  "pdf_path": "D:\\path\\to\\paper.pdf",
  "attachment_key": "ABC12345",
  "target_text": "text to highlight",
  "page": 0,
  "comment": "中文批注内容",
  "color": "#ffd400"
}

Note on paths:
  - Windows paths can use forward slashes: D:/Documents/...
  - Or double backslashes in JSON: "D:\\\\Documents\\\\..."
  - Both formats are automatically normalized
        """,
    )
    
    # Info mode - get PDF metadata
    parser.add_argument(
        "--info", "-i",
        metavar="PDF_PATH",
        help="Show PDF information (page count, dimensions) and exit",
    )
    
    # Search mode - find text across all pages
    parser.add_argument(
        "--search", "-s",
        nargs=2,
        metavar=("PDF_PATH", "QUERY"),
        help="Search for text across all PDF pages (pre-flight verification)",
    )
    
    # JSON file mode (for Unicode-safe input)
    parser.add_argument(
        "--json", "-j",
        metavar="FILE",
        help="Read parameters from a JSON file (recommended for Chinese comments)",
    )
    
    # Direct arguments
    parser.add_argument("pdf_path", nargs="?", help="Path to the PDF file")
    parser.add_argument("attachment_key", nargs="?", help="Zotero attachment key (e.g., SNX599P2)")
    parser.add_argument("target_text", nargs="?", help="Text to highlight in the PDF")
    parser.add_argument(
        "--page", "-p",
        type=int,
        default=0,
        help="Page index (0-based, default: 0)",
    )
    parser.add_argument(
        "--comment", "-c",
        default="",
        help="Comment to attach to the highlight (default: empty)",
    )
    parser.add_argument(
        "--color",
        default="#ffd400",
        help="Highlight color in hex format (default: #ffd400 yellow)",
    )

    args = parser.parse_args()

    # Info mode - show PDF metadata
    if args.info:
        return show_pdf_info(args.info)
    
    # Search mode - find text across all pages
    if args.search:
        return search_pdf_text(args.search[0], args.search[1])

    # JSON file mode
    if args.json:
        try:
            with open(args.json, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # If it's a single dict, wrap it in a list
            if isinstance(data, dict):
                data = [data]
            
            success_count = 0
            for params in data:
                try:
                    res = run_annotation(
                        pdf_path=params["pdf_path"],
                        attachment_key=params["attachment_key"],
                        target_text=params["target_text"],
                        page=params.get("page", 0),
                        comment=params.get("comment", ""),
                        color=params.get("color", "#ffd400"),
                    )
                    if res == 0:
                        success_count += 1
                except Exception as e:
                    print(f"Error processing annotation: {e}")
            
            return 0 if success_count > 0 else 1

        except FileNotFoundError:
            print(f"Error: JSON file not found: {args.json}")
            return 1
        except json.JSONDecodeError as e:
            print(f"Error: Invalid JSON file: {e}")
            return 1
        except KeyError as e:
            print(f"Error: Missing required field in JSON: {e}")
            return 1
    
    # Direct command line mode
    if not all([args.pdf_path, args.attachment_key, args.target_text]):
        parser.print_help()
        print("\nError: pdf_path, attachment_key, and target_text are required")
        return 1

    return run_annotation(
        pdf_path=args.pdf_path,
        attachment_key=args.attachment_key,
        target_text=args.target_text,
        page=args.page,
        comment=args.comment,
        color=args.color,
    )


if __name__ == "__main__":
    sys.exit(main())
