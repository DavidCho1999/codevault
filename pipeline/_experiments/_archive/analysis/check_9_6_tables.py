import json
import re

# Load JSON
with open('../codevault/public/data/part9.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find Section 9.6
section_9_6 = None
for section in data['sections']:
    if section['id'] == '9.6':
        section_9_6 = section
        break

if not section_9_6:
    print("[ERROR] Section 9.6 not found")
    exit(1)

print(f"[OK] Section 9.6 found: {section_9_6['title']}")
print(f"   Subsections: {len(section_9_6['subsections'])}\n")

# Check for tables in 9.6.1
subsection_9_6_1 = section_9_6['subsections'][0]
print(f"=== 9.6.1: {subsection_9_6_1['title']} ===")
print(f"Page: {subsection_9_6_1['page']}")

content = subsection_9_6_1['content']
print(f"Content length: {len(content)} characters")

# Check for table patterns
table_patterns = [
    r'Table\s+9\.\d+\.\d+\.\d+',  # "Table 9.6.1.1"
    r'table\s+9\.\d+\.\d+\.\d+',  # lowercase
    r'\|.*\|',  # Markdown table
    r'───',     # Table border
    r'^\s*\d+\.\s+\d+',  # Numbered rows
]

tables_found = []
for pattern in table_patterns:
    matches = re.findall(pattern, content, re.MULTILINE | re.IGNORECASE)
    if matches:
        tables_found.append((pattern, matches))

if tables_found:
    print(f"\n[OK] Tables found: {len(tables_found)} pattern(s) matched")
    for pattern, matches in tables_found:
        print(f"\n  Pattern: {pattern}")
        print(f"  Matches: {len(matches)}")
        # Show first 3 matches
        for match in matches[:3]:
            print(f"    - {match[:100]}")
else:
    print("\n[WARN] No table patterns found")
    print("\nFirst 500 characters of content:")
    print(content[:500])
    print("\n...")
    print("\nLast 500 characters of content:")
    print(content[-500:])

# Check all subsections for tables
print("\n\n=== All 9.6 Subsections Table Check ===")
for sub in section_9_6['subsections']:
    content = sub['content']
    has_table = any(re.search(p, content, re.IGNORECASE) for p in table_patterns)
    status = "[TABLE]" if has_table else "[TEXT] "
    print(f"{status} {sub['id']:8s} {sub['title']:50s} ({len(content):5d} chars)")
