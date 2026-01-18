import json
import re

# Load JSON
with open('../codevault/public/data/part9.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Find Section 9.6.1
section_9_6 = None
for section in data['sections']:
    if section['id'] == '9.6':
        section_9_6 = section
        break

subsection_9_6_1 = section_9_6['subsections'][0]
content = subsection_9_6_1['content']

# Extract Table 9.6.1.3 section
table_pattern = r'(Table 9\.6\.1\.3.*?)(?=\n9\.6\.1\.\d+\.|$)'
match = re.search(table_pattern, content, re.DOTALL | re.IGNORECASE)

if match:
    table_section = match.group(1)
    print("=== Table 9.6.1.3 Section ===")
    print(f"Length: {len(table_section)} characters\n")
    print(table_section[:2000])
    print("\n...\n")
    print(table_section[-500:])
else:
    print("[WARN] Table 9.6.1.3 not found in expected format")
    print("\nSearching for 'Table 9.6.1.3' occurrences:")
    for match in re.finditer(r'Table 9\.6\.1\.3', content, re.IGNORECASE):
        start = max(0, match.start() - 100)
        end = min(len(content), match.end() + 200)
        print(f"\n--- Found at position {match.start()} ---")
        print(content[start:end])
