#!/usr/bin/env python3
"""
Fix caption duplicate issue - Remove "Forming Part of..." from caption_html
Tables affected: 9.7.2.3, 9.7.3.3
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent / "codevault" / "public" / "data"
OVERRIDES_PATH = BASE_DIR / "manual_table_overrides.json"

def main():
    # Load overrides
    with open(OVERRIDES_PATH, 'r', encoding='utf-8') as f:
        overrides = json.load(f)

    # Fix 9.7.2.3
    if "9.7.2.3" in overrides:
        # Remove <br/>Forming Part of...
        new_caption = "<strong>Glass Areas for Rooms of Residential Occupancy</strong>"
        overrides["9.7.2.3"]["caption_html"] = new_caption
        print("[FIX] 9.7.2.3 caption updated")

    # Fix 9.7.3.3
    if "9.7.3.3" in overrides:
        # Remove <br/>Forming Part of...
        new_caption = "<strong>Maximum U-value or Minimum Temperature Index (I) for Windows, Doors and Skylights⁽¹⁾⁽²⁾⁽³⁾</strong>"
        overrides["9.7.3.3"]["caption_html"] = new_caption
        print("[FIX] 9.7.3.3 caption updated")

    # Save
    with open(OVERRIDES_PATH, 'w', encoding='utf-8') as f:
        json.dump(overrides, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Updated {OVERRIDES_PATH}")

if __name__ == "__main__":
    main()
