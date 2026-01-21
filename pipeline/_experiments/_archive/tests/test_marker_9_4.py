# -*- coding: utf-8 -*-
"""
Marker PDF 테스트 - Section 9.4 추출
현재 PyMuPDF 결과와 비교하기 위한 테스트
"""

import os
import sys

# PDF 경로
PDF_PATH = "source/2024 Building Code Compendium/301880.pdf"
OUTPUT_DIR = "scripts_temp/marker_output"

# 9.4 섹션 페이지 범위 (실제 확인됨: 721-724)
START_PAGE = 721
END_PAGE = 725

def test_marker():
    """Marker로 9.4 섹션 추출"""
    from marker.converters.pdf import PdfConverter
    from marker.models import create_model_dict
    from marker.config.parser import ConfigParser

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    print(f"Loading models...")

    # 설정
    config = {
        "output_format": "markdown",
        "page_range": f"{START_PAGE}-{END_PAGE}",  # 0-indexed가 아닐 수 있음
    }

    config_parser = ConfigParser(config)
    converter = PdfConverter(
        config=config_parser.generate_config_dict(),
        artifact_dict=create_model_dict(),
    )

    print(f"Converting pages {START_PAGE}-{END_PAGE}...")
    rendered = converter(PDF_PATH)

    # 결과 저장
    output_path = os.path.join(OUTPUT_DIR, "section_9_4.md")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(rendered.markdown)

    print(f"Saved to {output_path}")
    print(f"\n--- First 2000 chars ---")
    print(rendered.markdown[:2000])

    return rendered.markdown

def test_pymupdf():
    """비교용: PyMuPDF로 같은 페이지 추출"""
    import fitz

    doc = fitz.open(PDF_PATH)
    text = ""
    for i in range(START_PAGE, min(END_PAGE, len(doc))):
        text += doc[i].get_text()
    doc.close()

    output_path = os.path.join(OUTPUT_DIR, "section_9_4_pymupdf.txt")
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(text)

    print(f"PyMuPDF saved to {output_path}")
    return text

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "pymupdf":
        test_pymupdf()
    else:
        test_marker()
