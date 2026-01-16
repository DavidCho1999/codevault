"""
Part 9 샘플 페이지 텍스트 추출
- 실제 텍스트 구조 파악
- 파싱 패턴 확인
"""

import fitz
import os
import sys

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH = "../../source/2024 Building Code Compendium"
PDF_FILE = "301880.pdf"

def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.normpath(os.path.join(script_dir, BASE_PATH, PDF_FILE))

    doc = fitz.open(pdf_path)

    # Part 9 시작 페이지 (711) 근처 샘플 추출
    sample_pages = [710, 711, 712, 715, 768, 769]  # Part 9 시작, Section 9.1, Section 9.10

    for page_num in sample_pages:
        if page_num < len(doc):
            page = doc[page_num]
            text = page.get_text()

            print(f"\n{'='*60}")
            print(f"Page {page_num + 1} (0-indexed: {page_num})")
            print(f"{'='*60}")
            print(text[:2000])  # 처음 2000자만

    doc.close()

if __name__ == "__main__":
    main()
