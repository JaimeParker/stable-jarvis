"""
Notion to Obsidian migrator.
Handles fetching Notion pages via MCP and converting them to pure Markdown for Obsidian.
"""

from __future__ import annotations

import logging
import re
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import json

import httpx

logger = logging.getLogger(__name__)

@dataclass
class MigrationResult:
    """Result of a Notion page migration."""
    success: bool
    markdown_path: Optional[Path] = None
    image_count: int = 0
    error: Optional[str] = None

class NotionPageMigrator:
    """
    Migrates Notion pages to local Markdown files compatible with Obsidian.
    
    This class handles:
    1. Parsing Notion-flavored Markdown (from notion-fetch)
    2. Downloading and localizing images
    3. Normalizing LaTeX equations
    4. Converting Notion-specific syntax to Obsidian-friendly Markdown
    """
    
    def __init__(self, output_dir: Path | str, image_downloader = None):
        """
        Initialize the migrator.
        
        Args:
            output_dir: Directory where the Markdown file and assets will be saved.
            image_downloader: Optional function to download images. If None, uses httpx.
        """
        self.output_dir = Path(output_dir)
        self.assets_dir = self.output_dir / "assets"
        self.client = httpx.Client(follow_redirects=True, timeout=30.0)
        self.image_downloader = image_downloader
        
    def __enter__(self):
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.client.close()

    def _sanitize_filename(self, filename: str) -> str:
        """Remove invalid characters from filenames."""
        return re.sub(r'[\\/*?:"<>|]', "_", filename)

    def _slugify(self, text: str) -> str:
        """Create a URL-friendly slug from text."""
        text = text.lower()
        # Remove non-alphanumeric characters
        text = re.sub(r'[^a-z0-9\s-]', '', text)
        # Replace spaces and multiple hyphens with a single hyphen
        text = re.sub(r'[\s-]+', '-', text).strip('-')
        return text

    def _normalize_indentation(self, content: str) -> str:
        """
        Normalize indentation: convert tabs to 4 spaces.
        Preserves structural nesting while ensuring compatibility.
        """
        # Convert tabs to 4 spaces - this is standard for Markdown nesting
        return content.replace("\t", "    ")

    def _download_image(self, url: str, slug: str, index: int) -> Optional[Path]:
        """Download an image and return its local path relative to assets_dir."""
        try:
            # Extract extension or default to png
            ext = "png"
            if ".jpg" in url.lower() or ".jpeg" in url.lower():
                ext = "jpg"
            elif ".gif" in url.lower():
                ext = "gif"
            elif ".svg" in url.lower():
                ext = "svg"
            
            filename = f"{slug}_{index}.{ext}"
            local_path = self.assets_dir / filename
            
            self.assets_dir.mkdir(parents=True, exist_ok=True)
            
            if self.image_downloader:
                logger.info(f"Using custom downloader for {url[:50]}...")
                content = self.image_downloader(url)
                if content:
                    with open(local_path, "wb") as f:
                        f.write(content)
                    return Path("assets") / filename
                return None

            response = self.client.get(url)
            response.raise_for_status()
            
            with open(local_path, "wb") as f:
                f.write(response.content)
                
            return Path("assets") / filename
        except Exception as e:
            logger.error(f"Failed to download image {url}: {e}")
            return None

    def _search_equation(self, context: str, page_id: str) -> Optional[str]:
        """Try to find the full equation using search context."""
        try:
            # This would normally call notion-search via MCP. 
            # In this environment, I have to rely on the agent to provide search results 
            # or simulate the logic if I'm within a larger tool.
            # For now, I'll add a placeholder that can be hooked into the MCP calls.
            return None
        except:
            return None

    def process_content(self, raw_content: str, page_id: str, title: str) -> Tuple[str, int]:
        """
        Process raw Notion content into clean Markdown.
        """
        content = raw_content
        slug = self._slugify(title) or page_id
        
        # 1. Normalize indentation to fix 'jammed' look
        content = self._normalize_indentation(content)
        
        # 2. Convert Notion math syntax: $` ... `$ -> $ ... $
        content = re.sub(r'\$`([^`]+)`\$', r'$\1$', content)
        
        # 3. Handle images
        image_count = 0
        image_pattern = r'!\[([^\]]*)\]\((https?://[^\s\)]+)\)'
        
        def image_replacer(match):
            nonlocal image_count
            alt_text = match.group(1)
            url = match.group(2)
            logger.info(f"Processing image {image_count+1}: {url[:60]}...")
            local_rel_path = self._download_image(url, slug, image_count)
            if local_rel_path:
                image_count += 1
                return f'![{alt_text}]({local_rel_path})'
            return match.group(0)
            
        content = re.sub(image_pattern, image_replacer, content)
        
        # 4. Detect and mark empty equation blocks for healing
        # Matches $$ followed by any amount of whitespace (including newlines) and then $$
        # Marks them with a special token for the migrate_page loop to find
        empty_eq_pattern = r'\$\$\s*\n?\s*\n?\s*\$\$'
        content = re.sub(empty_eq_pattern, '$$ [EMPTY_EQUATION_BLOCK] $$', content)
        
        # Clean up Notion-specific tags
        content = re.sub(r'<span color="[^"]*_bg">([^<]+)</span>', r'==\1==', content)
        content = re.sub(r'<span[^>]*>([^<]+)</span>', r'\1', content)
        content = re.sub(r'<mention-user[^>]*></mention-user>', '', content)
        content = re.sub(r'<file[^>]*></file>', '', content)
        
        return content, image_count

    def migrate_page(self, fetch_result: Dict[str, Any], mcp_search_func = None) -> MigrationResult:
        """
        Migrate a page, with an optional search function to heal equations.
        """
        try:
            title = fetch_result.get("title", "Untitled")
            page_id = fetch_result.get("id") or fetch_result.get("url", "").split("/")[-1] or "page"
            raw_text = fetch_result.get("text", "")
            
            content_match = re.search(r'<content>(.*?)</content>', raw_text, re.DOTALL)
            if not content_match:
                return MigrationResult(success=False, error="No <content> tag")
            
            raw_content = content_match.group(1).strip()
            clean_content, img_count = self.process_content(raw_content, page_id, title)
            
            # --- Equation Patching Logic ---
            if mcp_search_func:
                # Find all marked empty blocks
                marker = "$$ [EMPTY_EQUATION_BLOCK] $$"
                while marker in clean_content:
                    idx = clean_content.find(marker)
                    # Get context (50 chars before)
                    start = max(0, idx - 100)
                    context = clean_content[start:idx].strip()
                    # Clean context for search: remove markdown formatting, take last few words
                    words = re.sub(r'[^\w\s]', ' ', context).split()
                    query = " ".join(words[-8:]) if words else title
                    
                    replacement = "$$ [HEALING_FAILED] $$" # Default
                    if query:
                        logger.info(f"Attempting to heal empty equation block with context: '{query}'")
                        search_results = mcp_search_func(query=query, page_url=page_id)
                        
                        # Try to find LaTeX in highlights
                        if search_results and 'results' in search_results:
                            for res in search_results['results']:
                                highlight = res.get('highlight', '')
                                # Look for something that looks like LaTeX: starts with \, contains math symbols
                                # We want to be greedy but stop at reasonable boundaries
                                math_match = re.search(r'([\\][^\n]*?[^\\])(?:\s|$)', highlight)
                                if math_match:
                                    eq_content = math_match.group(1).strip()
                                    replacement = f"$$\n{eq_content}\n$$"
                                    logger.info(f"Healed equation: {eq_content[:50]}...")
                                    break
                    
                    clean_content = clean_content[:idx] + replacement + clean_content[idx+len(marker):]
            # --- End Patching ---
            
            # Prepare frontmatter
            properties = {}
            prop_match = re.search(r'<properties>(.*?)</properties>', raw_text, re.DOTALL)
            if prop_match:
                try:
                    properties = json.loads(prop_match.group(1).strip())
                except:
                    pass
            
            frontmatter = {
                "title": title,
                "notion_url": fetch_result.get("url"),
                "migrated_at": "2026-03-04", # Hardcoded for now, should use datetime
            }
            frontmatter.update(properties)
            
            # Write to file
            filename = self._sanitize_filename(title) + ".md"
            output_path = self.output_dir / filename
            self.output_dir.mkdir(parents=True, exist_ok=True)
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write("---\n")
                for k, v in frontmatter.items():
                    if isinstance(v, list):
                        f.write(f"{k}:\n")
                        for item in v:
                            f.write(f"  - {item}\n")
                    elif isinstance(v, dict):
                        f.write(f"{k}: {json.dumps(v, ensure_ascii=False)}\n")
                    else:
                        f.write(f"{k}: {v}\n")
                f.write("---\n\n")
                f.write(clean_content)
                
            return MigrationResult(success=True, markdown_path=output_path, image_count=img_count)
            
        except Exception as e:
            return MigrationResult(success=False, error=str(e))
