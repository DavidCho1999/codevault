"""
Update part10.json with Docling-extracted tables
"""
import json
import re

# Read Docling tables
with open('scripts_temp/docling_output/part10_table_6.md', 'r', encoding='utf-8') as f:
    table_a_md = f.read()

with open('scripts_temp/docling_output/part10_table_7.md', 'r', encoding='utf-8') as f:
    table_b_md = f.read()

def md_table_to_html(md_table, table_class="obc-table"):
    """Convert markdown table to HTML"""
    lines = [l.strip() for l in md_table.strip().split('\n') if l.strip()]
    if len(lines) < 2:
        return md_table

    html = f'<table class="{table_class}">'

    # Header row
    header_cells = [c.strip() for c in lines[0].split('|')[1:-1]]
    html += '<thead><tr>'
    for cell in header_cells:
        html += f'<th>{cell}</th>'
    html += '</tr></thead>'

    # Body rows (skip separator line)
    html += '<tbody>'
    for line in lines[2:]:
        cells = [c.strip() for c in line.split('|')[1:-1]]
        html += '<tr>'
        for cell in cells:
            html += f'<td>{cell}</td>'
        html += '</tr>'
    html += '</tbody></table>'

    return html

# Convert to HTML
table_a_html = md_table_to_html(table_a_md)
table_b_html = md_table_to_html(table_b_md)

print("Table 10.3.2.2.-A (Docling):")
print(table_a_html[:500])
print("\n...")

print("\nTable 10.3.2.2.-B (Docling):")
print(table_b_html[:500])

# Read part10.json
with open('codevault/public/data/part10.json', 'r', encoding='utf-8') as f:
    part10 = json.load(f)

# Find and replace tables in 10.3.2 content
for section in part10['sections']:
    for subsection in section.get('subsections', []):
        if subsection['id'] == '10.3.2':
            content = subsection['content']

            # Replace Table 10.3.2.2.-A
            old_table_a = re.search(r'<table class="obc-table">.*?</table>', content, re.DOTALL)
            if old_table_a:
                new_content = content[:old_table_a.start()] + table_a_html + content[old_table_a.end():]

                # Find and replace Table 10.3.2.2.-B (second table)
                old_table_b = re.search(r'<table class="obc-table">.*?</table>', new_content[old_table_a.start() + len(table_a_html):], re.DOTALL)
                if old_table_b:
                    insert_pos = old_table_a.start() + len(table_a_html) + old_table_b.start()
                    new_content = new_content[:insert_pos] + table_b_html + new_content[insert_pos + old_table_b.end() - old_table_b.start():]

                subsection['content'] = new_content
                print("\n[OK] Tables replaced in 10.3.2")

# Save updated JSON
with open('codevault/public/data/part10.json', 'w', encoding='utf-8') as f:
    json.dump(part10, f, ensure_ascii=False, indent=2)

print("\n[OK] part10.json updated with Docling tables!")
