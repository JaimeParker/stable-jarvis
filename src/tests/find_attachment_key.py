"""Find the correct PDF attachment Item Key in Zotero."""
from stable_jarvis import ZoteroClient, get_default_config

# Use the package's configuration loading
config = get_default_config()
client = ZoteroClient(config)

# Access the underlying pyzotero instance
zot = client._zot

# Get children of SNX599P2 (annotations under the PDF)
print("Listing annotations under PDF SNX599P2...\n")
children = zot.children("SNX599P2")

for item in children:
    key = item["key"]
    data = item["data"]
    item_type = data.get("itemType", "?")
    annot_type = data.get("annotationType", "-")
    annot_text = data.get("annotationText", "")[:60]
    annot_pos = data.get("annotationPosition", "")
    
    print(f"Key: {key}")
    print(f"  itemType: {item_type}")
    print(f"  annotationType: {annot_type}")
    print(f"  annotationText: {annot_text}")
    print(f"  annotationPosition: {annot_pos}")
    print()

if not children:
    print("No children found under SNX599P2")
