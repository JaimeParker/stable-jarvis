#!/usr/bin/env python3
import sys
import json
import re
from pathlib import Path
from stable_jarvis import NotionPageMigrator

def main():
    if len(sys.argv) < 2:
        print("Usage: python migrate.py <notion_fetch_json_path> [output_dir] [heals_json_path]")
        sys.exit(1)
    
    json_path = Path(sys.argv[1])
    output_dir = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("./temp")
    heals_path = Path(sys.argv[3]) if len(sys.argv) > 3 else None
    
    heals = {}
    if heals_path and heals_path.exists():
        with open(heals_path, "r", encoding="utf-8") as f:
            heals = json.load(f)

    # Mock search function that uses provided heals
    def mock_search(query, page_url):
        # The agent provides heals indexed by a snippet of the context or a simple counter
        # For simplicity, we'll just check if any heal key is in the query or vice-versa
        for k, v in heals.items():
            if k in query or query in k:
                return {"results": [{"highlight": v}]}
        return {"results": []}

    with NotionPageMigrator(output_dir=output_dir) as migrator:
        with open(json_path, "r", encoding="utf-8") as f:
            fetch_result = json.load(f)
        
        # Run migration with the healing function
        result = migrator.migrate_page(fetch_result, mcp_search_func=mock_search)
        
        if result.success:
            print(f"Successfully migrated page to {result.markdown_path}")
            print(f"Downloaded {result.image_count} images.")
            
            # Post-process: ensure any unhealed blocks are cleaned up or left as markers
            # This is a safety net
            
            # Auto-clean JSON
            try:
                json_path.unlink()
                print(f"Cleaned up {json_path}")
                if heals_path and heals_path.exists():
                    heals_path.unlink()
                    print(f"Cleaned up {heals_path}")
            except Exception as e:
                print(f"Failed to clean up temporary files: {e}")
        else:
            print(f"Migration failed: {result.error}")

if __name__ == "__main__":
    main()
