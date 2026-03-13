"""
High-level management for Notion to Obsidian migration.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Dict, Any, Optional

from .migrator import NotionPageMigrator, MigrationResult

logger = logging.getLogger(__name__)

class NotionMigrationManager:
    """
    Manager class to orchestrate the migration of Notion pages.
    """
    
    def __init__(self, output_dir: Path | str, image_downloader = None):
        self.output_dir = Path(output_dir)
        self.migrator = NotionPageMigrator(self.output_dir, image_downloader=image_downloader)
        
    def migrate_single_page(self, fetch_result: Dict[str, Any]) -> MigrationResult:
        """
        Migrates a single Notion page using the provided fetch result.
        
        Args:
            fetch_result: The JSON dictionary returned by notion-fetch.
            
        Returns:
            MigrationResult containing the status and output path.
        """
        logger.info(f"Starting migration for page: {fetch_result.get('title', 'Untitled')}")
        return self.migrator.migrate_page(fetch_result)

    def batch_migrate(self, fetch_results: list[Dict[str, Any]]) -> list[MigrationResult]:
        """
        Migrates multiple Notion pages.
        """
        results = []
        for fetch_result in fetch_results:
            results.append(self.migrate_single_page(fetch_result))
        return results
