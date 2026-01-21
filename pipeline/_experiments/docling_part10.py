"""
Docling Part 10 Table Extraction (페이지 1030-1050)
"""
import os
import time
from pathlib import Path

os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import fitz
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorDevice, AcceleratorOptions

# Paths
PDF_PATH = Path(r"C:\Users\A\Desktop\lab\upcode-clone\source\2024 Building Code Compendium\301880.pdf")
OUTPUT_DIR = Path(r"C:\Users\A\Desktop\lab\upcode-clone\scripts_temp\docling_output")
TEMP_PDF = OUTPUT_DIR / "part10_pages.pdf"

# Extract Part 10 pages (1030-1050)
print("Extracting Part 10 pages (1030-1050)...")
src_pdf = fitz.open(PDF_PATH)
dst_pdf = fitz.open()

for page_num in range(1029, 1050):  # 0-indexed
    dst_pdf.insert_pdf(src_pdf, from_page=page_num, to_page=page_num)

dst_pdf.save(TEMP_PDF)
dst_pdf.close()
src_pdf.close()
print(f"Saved {TEMP_PDF.name} ({TEMP_PDF.stat().st_size // 1024} KB)")

# Docling conversion
print("\nRunning Docling with GPU...")
accelerator_options = AcceleratorOptions(
    num_threads=4,
    device=AcceleratorDevice.CUDA
)

pipeline_options = PdfPipelineOptions(
    accelerator_options=accelerator_options
)

converter = DocumentConverter(
    format_options={
        InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
    }
)

start_time = time.time()
result = converter.convert(TEMP_PDF)
elapsed = time.time() - start_time

print(f"Conversion completed in {elapsed:.1f}s")

# Get document
doc = result.document
tables = list(doc.tables)
print(f"Found {len(tables)} tables")

# Save markdown
md_output = OUTPUT_DIR / "part10_docling.md"
md_content = doc.export_to_markdown()
md_output.write_text(md_content, encoding='utf-8')
print(f"Saved to {md_output}")

# Show tables preview
print("\n" + "=" * 60)
for i, table in enumerate(tables[:10]):
    print(f"\n--- Table {i+1} ---")
    table_md = table.export_to_markdown()
    print(table_md[:600])

    # Save individual table
    (OUTPUT_DIR / f"part10_table_{i+1}.md").write_text(table_md, encoding='utf-8')

print(f"\nTotal tables: {len(tables)}")
