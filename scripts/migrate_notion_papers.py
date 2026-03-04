import os
import re
import shutil
import urllib.parse

source_root = "D:/Downloads/notion pages/ExportBlock/Papers"
obsidian_root = "D:/Projects/JARVIS-Dev"
literature_root = f"{obsidian_root}/30 Zettelkasten/31 Literature"
assets_root = f"{obsidian_root}/40 Resources/42 Assets/Images/Papers"

# Ensure assets directory exists
os.makedirs(assets_root, exist_ok=True)

# Map notion folder name to target obsidian folder name
category_map = {
    "AEROM": "AEROM",
    "MP and Agile Flight": "MP and Agile Flight",
    "RFT and RL-Gen Model Papers": "RFT and RL-Gen Model Papers",
    "RL Master": "RL Master",
    "鍏疯韩": "Embodied AI" # This is "具身" in some encoding
}

def clean_name(name):
    # Remove Notion ID (32 hex characters at the end)
    return re.sub(r' [a-f0-9]{32}$', '', name).strip()

def process_file(file_path, target_dir, category):
    filename = os.path.basename(file_path)
    if not filename.endswith(".md"):
        return
    
    clean_title = clean_name(filename[:-3])
    target_path = os.path.join(target_dir, clean_title + ".md")
    
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Extract metadata
    lines = content.split('\n')
    frontmatter = {
        "title": clean_title,
        "category": category,
        "tags": []
    }
    
    meta_end_idx = 0
    # Simple parser for the header properties
    for i, line in enumerate(lines):
        if i == 0 and line.startswith("# "):
            continue
        if ":" in line and i < 15: # Look at first 15 lines for metadata
            key_val = line.split(":", 1)
            if len(key_val) == 2:
                key, val = key_val
                key = key.strip().lower()
                val = val.strip()
                if key == "status":
                    frontmatter["status"] = val
                elif key == "tags":
                    frontmatter["tags"] = [t.strip() for t in val.split(",")]
                elif key == "remarks":
                    frontmatter["remarks"] = val
                elif key == "links/doi":
                    frontmatter["url"] = val
                elif key == "jour/conf":
                    frontmatter["journal"] = val
                meta_end_idx = i
        elif line.strip() == "---":
             meta_end_idx = i
             break
        elif i > 15:
            break

    # Build new frontmatter
    fm_str = "---\n"
    for k, v in frontmatter.items():
        if isinstance(v, list):
            fm_str += f"{k}: [{', '.join(v)}]\n"
        else:
            fm_str += f"{k}: \"{v}\"\n"
    fm_str += "---\n\n"
    
    # Clean content: remove the original header lines
    actual_content = "\n".join(lines[meta_end_idx+1:])
    
    # Handle images
    def img_replace(match):
        alt_text = match.group(1)
        img_url = match.group(2)
        decoded_url = urllib.parse.unquote(img_url)
        img_name = os.path.basename(decoded_url)
        safe_title = clean_title.encode('ascii', 'ignore').decode('ascii').replace(' ', '_')
        if not safe_title: safe_title = "paper_image"
        new_img_name = f"{safe_title}_{img_name}"
        
        src_img_path = os.path.join(os.path.dirname(file_path), decoded_url)
        if os.path.exists(src_img_path):
            dest_img_path = os.path.join(assets_root, new_img_name)
            shutil.copy2(src_img_path, dest_img_path)
            # Use wikilinks for Obsidian preference if possible, but keeping path for now
            return f"![{alt_text}](../../../40%20Resources/42%20Assets/Images/Papers/{new_img_name})"
        return match.group(0)

    actual_content = re.sub(r'!\[(.*?)\]\((.*?)\)', img_replace, actual_content)
    
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write(fm_str + actual_content)

def main():
    source_dirs = os.listdir(source_root)
    for d in source_dirs:
        src_dir = os.path.join(source_root, d)
        if not os.path.isdir(src_dir):
            continue
            
        target_folder_name = None
        if d in category_map:
            target_folder_name = category_map[d]
        elif any(c in d for c in ["具身", "鍏疯韩"]):
            target_folder_name = "Embodied AI"
        else:
            # Fallback for unknown folders
            target_folder_name = d
            
        dest_dir = os.path.join(literature_root, target_folder_name)
        os.makedirs(dest_dir, exist_ok=True)
        
        print(f"Processing {d} -> {target_folder_name}")
        for item in os.listdir(src_dir):
            if item.endswith(".md"):
                process_file(os.path.join(src_dir, item), dest_dir, target_folder_name)

if __name__ == "__main__":
    main()
