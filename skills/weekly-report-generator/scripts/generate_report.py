import os
import datetime
from typing import List, Dict

def get_week_range(today: datetime.date) -> List[datetime.date]:
    """
    Returns a list of dates from the previous Saturday to today (Saturday).
    If today is Saturday, the range is 8 days (Sat to Sat).
    """
    # User requested: "UserName_2026_0221_0228_week_report.pptx"
    # 0221 is the previous Saturday. 0228 is today.
    # We want Feb 21, 22, 23, 24, 25, 26, 27, 28.
    
    # Calculate days since previous Saturday
    # weekday(): Monday is 0, Sunday is 6. Saturday is 5.
    days_to_subtract = (today.weekday() - 5) % 7
    if days_to_subtract == 0: # Today is Saturday
        days_to_subtract = 7 # Go back one week
    
    start_date = today - datetime.timedelta(days=7)
    
    date_list = []
    for i in range(8): # From start_date to today inclusive
        date_list.append(start_date + datetime.timedelta(days=i))
    return date_list

def find_daily_notes(vault_path: str, dates: List[datetime.date]) -> Dict[str, str]:
    notes = {}
    daily_notes_dir = os.path.join(vault_path, "50 Archive", "Daily Notes")
    
    for date in dates:
        filename = f"{date.isoformat()}.md" # YYYY-MM-DD.md
        filepath = os.path.join(daily_notes_dir, filename)
        if os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                notes[date.isoformat()] = f.read()
    return notes

def summarize_notes(notes: Dict[str, str]) -> str:
    # This part will be handled by the Agent using the extracted notes.
    # But we can provide a structured output.
    output = []
    for date, content in sorted(notes.items()):
        output.append(f"### {date}")
        output.append(content)
        output.append("
---
")
    return "
".join(output)

if __name__ == "__main__":
    # For testing, we use the date provided by the user: 2026-02-28
    today = datetime.date(2026, 2, 28)
    dates = get_week_range(today)
    
    # Vault path - in this environment it seems to be the current directory 
    # if we are running from the root of the project, but Obsidian tools 
    # work with a specific vault. The agent will provide the content.
    print(f"Report Range: {dates[0]} to {dates[-1]}")
    for d in dates:
        print(d.isoformat())
