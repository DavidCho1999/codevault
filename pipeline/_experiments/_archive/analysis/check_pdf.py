import fitz

# Check 301880.pdf (Part 9)
pdf = fitz.open(r'C:/Users/A/Desktop/lab/upcode-clone/source/2024 Building Code Compendium/301880.pdf')
print(f"301880.pdf: {len(pdf)} pages")

for i in range(len(pdf)):
    text = pdf[i].get_text()
    if 'Table 10.3.2.2' in text:
        print(f'Page {i+1}: Table 10.3.2.2 found!')
        with open('scripts_temp/part10_table_page.txt', 'w', encoding='utf-8') as f:
            f.write(text)
        break
    if 'Part 10' in text and 'Change of Use' in text and i > 10:
        print(f'Page {i+1}: Part 10 Change of Use')
