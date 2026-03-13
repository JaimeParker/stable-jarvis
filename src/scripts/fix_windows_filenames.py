import os
import re

lit_root = 'D:/Documents/Cyber Brain/30 Zettelkasten/31 Literature'

def sanitize_for_windows(name):
    # Remove colons and other forbidden chars
    return re.sub(r'[\/*?:"<>|]', '', name).strip()

def fix_titles_and_filenames():
    for root, dirs, files in os.walk(lit_root):
        for file in files:
            if not file.endswith('.md'): continue
            
            file_path = os.path.join(root, file)
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 1. Find the real full title from the first # heading
            full_title = ""
            match_heading = re.search(r'^# (.*)', content, re.MULTILINE)
            if match_heading:
                full_title = match_heading.group(1).strip()
            
            if not full_title:
                # Fallback to current frontmatter title
                match_fm = re.search(r'^title: "(.*?)"', content, re.MULTILINE)
                if match_fm:
                    full_title = match_fm.group(1).strip()
                else:
                    full_title = file[:-3]

            # 2. Update Frontmatter (Keep Colons)
            new_content = re.sub(r'^title: ".*?"', f'title: "{full_title}"', content, flags=re.MULTILINE)
            
            if new_content != content:
                with open(file_path, 'w', encoding='utf-8') as f:
                    f.write(new_content)
            
            # 3. Rename Filename (Remove Colons)
            safe_name = sanitize_for_windows(full_title)
            new_path = os.path.join(root, safe_name + '.md')
            
            if file_path != new_path:
                print(f"Renaming: {file} -> {safe_name}.md")
                if os.path.exists(new_path):
                    os.remove(file_path) # Remove the old fragmented version
                else:
                    os.rename(file_path, new_path)

if __name__ == "__main__":
    fix_titles_and_filenames()
