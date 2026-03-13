import os
import re

lit_root = 'D:/Documents/Cyber Brain/30 Zettelkasten/31 Literature'

def sanitize_tags(match):
    prefix = match.group(1)
    tags_data = match.group(2)
    suffix = match.group(3)
    
    # Split by comma, strip each tag, replace space with underscore
    tags = [t.strip().replace(' ', '_') for t in tags_data.split(',') if t.strip()]
    return f"{prefix}{', '.join(tags)}{suffix}"

def main():
    for root, dirs, files in os.walk(lit_root):
        for file in files:
            if not file.endswith('.md'): continue
            
            path = os.path.join(root, file)
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Match frontmatter tags: [tag 1, tag 2]
            new_content = re.sub(r'^(tags:\s*\[)(.*?)(\])', sanitize_tags, content, flags=re.MULTILINE)
            
            if new_content != content:
                print(f"Updating tags in: {file}")
                with open(path, 'w', encoding='utf-8') as f:
                    f.write(new_content)

if __name__ == "__main__":
    main()
