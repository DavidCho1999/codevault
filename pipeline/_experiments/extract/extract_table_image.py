#!/usr/bin/env python3
"""
PDF에서 테이블 영역만 이미지로 추출
- pdfplumber: 테이블 위치 감지
- PyMuPDF: 해당 영역 이미지 추출
"""

import fitz
import pdfplumber
from pathlib import Path

PDF_PATH = Path(__file__).parent.parent / "source" / "2024 Building Code Compendium" / "301880.pdf"
OUTPUT_DIR = Path(__file__).parent


def extract_table_image(page_num: int, table_index: int = 0, zoom: float = 3.0, padding: int = 10):
    """
    PDF 페이지에서 테이블 영역만 이미지로 추출

    Args:
        page_num: 페이지 번호 (1-indexed)
        table_index: 페이지 내 테이블 인덱스 (0부터)
        zoom: 이미지 해상도 배율
        padding: 테이블 주변 여백 (pixels)
    """
    page_idx = page_num - 1  # 0-indexed

    # 1. pdfplumber로 테이블 위치 감지
    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[page_idx]
        tables = page.find_tables()

        if not tables:
            print(f"[X] No tables found on page {page_num}")
            return None

        if table_index >= len(tables):
            print(f"[X] Table index {table_index} out of range (found {len(tables)} tables)")
            return None

        bbox = tables[table_index].bbox
        print(f"[1] Found table at bbox: {bbox}")

    # 2. PyMuPDF로 해당 영역 추출
    doc = fitz.open(PDF_PATH)
    page = doc[page_idx]

    # bbox에 padding 추가
    x0, y0, x1, y1 = bbox
    table_rect = fitz.Rect(
        max(0, x0 - padding),
        max(0, y0 - padding),
        min(page.rect.width, x1 + padding),
        min(page.rect.height, y1 + padding)
    )

    # 고해상도 이미지 추출
    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat, clip=table_rect)

    # 저장
    output_path = OUTPUT_DIR / f"table_p{page_num}_t{table_index}.png"
    pix.save(str(output_path))

    print(f"[2] Saved: {output_path}")
    print(f"    Size: {pix.width}x{pix.height}")

    doc.close()
    return output_path


def list_tables_on_page(page_num: int):
    """페이지의 모든 테이블 위치 출력"""
    page_idx = page_num - 1

    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[page_idx]
        tables = page.find_tables()

        print(f"Page {page_num}: {len(tables)} table(s)")
        for i, t in enumerate(tables):
            print(f"  [{i}] bbox: {t.bbox}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage:")
        print("  python extract_table_image.py <page_num> [table_index]")
        print("  python extract_table_image.py list <page_num>")
        print("")
        print("Examples:")
        print("  python extract_table_image.py 718        # Extract first table from page 718")
        print("  python extract_table_image.py 718 1      # Extract second table")
        print("  python extract_table_image.py list 718   # List all tables on page")
        sys.exit(1)

    if sys.argv[1] == "list":
        page_num = int(sys.argv[2])
        list_tables_on_page(page_num)
    else:
        page_num = int(sys.argv[1])
        table_index = int(sys.argv[2]) if len(sys.argv) > 2 else 0
        extract_table_image(page_num, table_index)
