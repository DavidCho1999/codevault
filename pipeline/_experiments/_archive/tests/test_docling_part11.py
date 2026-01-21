"""
Docling Part 11 Table Extraction Test (GPU Mode)
=================================================
Part 11: Renovation (301881.pdf)
Docling v2.68.0 with CUDA
"""

import time
import os
from pathlib import Path

# Force CUDA
os.environ["CUDA_VISIBLE_DEVICES"] = "0"

import torch
print(f"PyTorch CUDA: {torch.cuda.is_available()}")
print(f"Device: {torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'CPU'}")

# Docling imports
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, AcceleratorDevice, AcceleratorOptions

# PDF path
PDF_PATH = Path(r"C:\Users\A\Desktop\lab\upcode-clone\source\2024 Building Code Compendium\301881.pdf")
OUTPUT_DIR = Path(r"C:\Users\A\Desktop\lab\upcode-clone\scripts_temp\docling_output")
OUTPUT_DIR.mkdir(exist_ok=True)

def main():
    print("=" * 60)
    print("Docling Part 11 Table Extraction Test (GPU Mode)")
    print("=" * 60)

    # Configure for GPU acceleration
    accelerator_options = AcceleratorOptions(
        num_threads=4,
        device=AcceleratorDevice.CUDA  # Use GPU
    )

    pipeline_options = PdfPipelineOptions(
        accelerator_options=accelerator_options
    )

    # Create converter with GPU settings using correct API
    converter = DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options)
        }
    )

    print(f"\nProcessing: {PDF_PATH.name}")
    print(f"File size: {PDF_PATH.stat().st_size / 1024 / 1024:.1f} MB")
    print("Using GPU acceleration...")

    # Convert document
    start_time = time.time()
    result = converter.convert(PDF_PATH)
    elapsed = time.time() - start_time

    print(f"\nConversion completed in {elapsed:.1f} seconds ({elapsed/60:.1f} min)")

    # Get document
    doc = result.document

    # Count tables
    tables = list(doc.tables)
    print(f"\nFound {len(tables)} tables")

    # Export to markdown
    md_output = OUTPUT_DIR / "part11_docling.md"
    md_content = doc.export_to_markdown()
    md_output.write_text(md_content, encoding='utf-8')
    print(f"Markdown saved to: {md_output}")

    # Export tables preview
    print("\n" + "=" * 60)
    print("First 5 Tables Preview:")
    print("=" * 60)

    for i, table in enumerate(tables[:5]):
        print(f"\n--- Table {i+1} ---")
        table_md = table.export_to_markdown()
        print(table_md[:800] + "..." if len(table_md) > 800 else table_md)

        # Save individual table
        table_file = OUTPUT_DIR / f"table_{i+1}.md"
        table_file.write_text(table_md, encoding='utf-8')

    print("\n" + "=" * 60)
    print("Summary")
    print("=" * 60)
    print(f"Total tables: {len(tables)}")
    print(f"Processing time: {elapsed:.1f}s ({elapsed/60:.1f} min)")
    print(f"Output directory: {OUTPUT_DIR}")

if __name__ == "__main__":
    main()
