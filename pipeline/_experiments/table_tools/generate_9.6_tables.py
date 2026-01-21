#!/usr/bin/env python3
"""
Generate manual_table_overrides.json entries for Tables 9.6.1.3.-B through -G
Based on part9.json content data
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent / "codevault" / "public" / "data"

# Table metadata (from part9.json content)
TABLES = {
    "9.6.1.3.-B": {
        "title": "Maximum Glass Area for Windows in Areas for which the 1-in-50 Hourly Wind Pressure (HWP) is Less than 0.75 kPa⁽¹⁾",
        "subtitle": "Forming Part of Clause 9.6.1.3.(2)(a)",
        "page": 731,
        "rows": 8,  # 3 header + 5 data
        "types": ["Annealed", "Factory-sealed insulated glass (IG) units⁽²⁾", "Heat-strengthened", "Tempered", "Wired"]
    },
    "9.6.1.3.-C": {
        "title": "Maximum Glass Area for Windows in Areas for which the 1-in-50 Hourly Wind Pressure (HWP) is Less than 1.00 kPa⁽¹⁾",
        "subtitle": "Forming Part of Clause 9.6.1.3.(2)(a)",
        "page": 731,
        "rows": 8,
        "types": ["Annealed", "Factory-sealed insulated glass (IG) units⁽²⁾", "Heat-strengthened", "Tempered", "Wired"]
    },
    "9.6.1.3.-D": {
        "title": "Maximum Glass Area for Windows in Areas for which the 1-in-50 Hourly Wind Pressure (HWP) is Less than 0.55 kPa – Open Terrain⁽¹⁾",
        "subtitle": "Forming Part of Clause 9.6.1.3.(2)(b)",
        "page": 732,
        "rows": 8,
        "types": ["Annealed", "Factory-sealed insulated glass (IG) units⁽²⁾", "Heat-strengthened", "Tempered", "Wired"]
    },
    "9.6.1.3.-E": {
        "title": "Maximum Glass Area for Windows in Areas for which the 1-in-50 Hourly Wind Pressure (HWP) is Less than 0.75 kPa – Open Terrain⁽¹⁾",
        "subtitle": "Forming Part of Clause 9.6.1.3.(2)(b)",
        "page": 732,
        "rows": 8,
        "types": ["Annealed", "Factory-sealed insulated glass (IG) units⁽²⁾", "Heat-strengthened", "Tempered", "Wired"]
    },
    "9.6.1.3.-F": {
        "title": "Maximum Glass Area for Windows in Areas for which the 1-in-50 Hourly Wind Pressure (HWP) is Less than 1.00 kPa – Open Terrain⁽¹⁾",
        "subtitle": "Forming Part of Clause 9.6.1.3.(2)(b)",
        "page": 732,
        "rows": 8,
        "types": ["Annealed", "Factory-sealed insulated glass (IG) units⁽²⁾", "Heat-strengthened", "Tempered", "Wired"]
    }
}

# Data from part9.json content (manually extracted)
TABLE_DATA = {
    "9.6.1.3.-B": [
        ["0.42", "0.68", "1.02", "1.42", "2.04", "3.34", "4.70", "7.65"],
        ["0.72", "1.19", "1.85", "2.56", "3.64", "6.01", "8.35", "11.83"],
        ["0.88", "1.46", "2.21", "2.71", "3.39", "4.73", "5.92", "8.29"],
        ["1.18", "1.64", "2.21", "2.71", "3.39", "4.73", "5.92", "8.29"],
        ["0.20", "0.32", "0.50", "0.68", "0.94", "1.55", "2.19", "3.60"]
    ],
    "9.6.1.3.-C": [
        ["0.30", "0.50", "0.77", "1.05", "1.45", "2.40", "3.40", "5.62"],
        ["0.52", "0.86", "1.31", "1.86", "2.57", "4.30", "6.10", "9.89"],
        ["0.65", "1.04", "1.63", "2.26", "2.92", "4.07", "5.10", "7.14"],
        ["1.01", "1.42", "1.90", "2.33", "2.92", "4.07", "5.10", "7.14"],
        ["0.16", "0.26", "0.38", "0.52", "0.71", "1.15", "1.63", "2.69"]
    ],
    "9.6.1.3.-D": [
        ["0.46", "0.75", "1.16", "1.60", "2.25", "3.76", "5.32", "8.70"],
        ["0.80", "1.34", "2.11", "2.93", "4.10", "6.90", "9.66", "12.53"],
        ["0.98", "1.74", "2.33", "2.86", "3.59", "5.00", "6.26", "8.78"],
        ["1.25", "1.74", "2.33", "2.86", "3.59", "5.00", "6.26", "8.78"],
        ["0.22", "0.36", "0.55", "0.76", "1.05", "1.75", "2.47", "4.09"]
    ],
    "9.6.1.3.-E": [
        ["0.33", "0.54", "0.83", "1.14", "1.61", "2.67", "3.75", "6.14"],
        ["0.57", "0.94", "1.47", "2.04", "2.85", "4.75", "6.72", "10.97"],
        ["0.70", "1.15", "1.79", "2.44", "3.06", "4.36", "5.34", "7.47"],
        ["1.06", "1.48", "1.99", "2.44", "3.06", "4.36", "5.34", "7.47"],
        ["0.16", "0.26", "0.40", "0.55", "0.76", "1.24", "1.77", "2.93"]
    ],
    "9.6.1.3.-F": [
        ["0.25", "0.40", "0.62", "0.84", "1.17", "1.94", "2.75", "4.50"],
        ["0.42", "0.68", "1.04", "1.46", "2.05", "3.41", "4.87", "7.92"],
        ["0.51", "0.84", "1.30", "1.79", "2.52", "3.69", "4.60", "6.44"],
        ["0.92", "1.28", "1.72", "2.10", "2.63", "3.69", "4.60", "6.44"],
        ["0.12", "0.20", "0.30", "0.41", "0.57", "0.94", "1.31", "2.18"]
    ]
}

NOTES_HTML = """<div class="table-notes mt-2 text-sm text-gray-600"><p class="font-semibold">Notes to Table {table_id}:</p><p>(1) The maximum hourly wind pressure with one chance in fifty of being exceeded in any one year, as provided in MMAH Supplementary Standard SB-1, "Climatic and Seismic Data."</p><p>(2) Maximum glass area values apply to IG units of two identical lites (annealed, heat-strengthened or tempered) spaced at 12.7 mm.</p></div>"""


def generate_table_override(table_id):
    """Generate override entry for a single table"""
    meta = TABLES[table_id]
    data_rows = TABLE_DATA[table_id]

    # Build data array (3 header rows + 5 data rows)
    data = [
        ["Type of Glass", "Maximum Glass Area, m²", None, None, None, None, None, None, None],
        [None, "Glass Thickness, mm", None, None, None, None, None, None, None],
        [None, "2.5", "3", "4", "5", "6", "8", "10", "12"]
    ]

    # Add data rows
    for i, glass_type in enumerate(meta["types"]):
        row = [glass_type] + data_rows[i]
        data.append(row)

    return {
        "title": f"Table {table_id}",
        "page": meta["page"],
        "cols": 9,
        "rows": meta["rows"],
        "header_rows": 3,
        "caption_html": f"<strong>{meta['title']}</strong><br/>{meta['subtitle']}",
        "data": data,
        "spans": {
            "rowspans": [
                {"row": 0, "col": 0, "span": 3}
            ],
            "colspans": [
                {"row": 0, "col": 1, "span": 8},
                {"row": 1, "col": 1, "span": 8}
            ]
        },
        "notes_html": NOTES_HTML.format(table_id=table_id),
        "notes": "Complete data with rowspan/colspan structure - fixed MERGE errors"
    }


def main():
    # Load existing overrides
    overrides_path = BASE_DIR / "manual_table_overrides.json"
    with open(overrides_path, 'r', encoding='utf-8') as f:
        overrides = json.load(f)

    # Add new tables
    for table_id in TABLES.keys():
        overrides[table_id] = generate_table_override(table_id)
        print(f"[+] Generated override for Table {table_id}")

    # Save
    with open(overrides_path, 'w', encoding='utf-8') as f:
        json.dump(overrides, f, ensure_ascii=False, indent=2)

    print(f"\n[OK] Updated {overrides_path}")
    print(f"[OK] Added {len(TABLES)} table overrides")


if __name__ == "__main__":
    main()
