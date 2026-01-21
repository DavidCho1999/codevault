"""
2-Column 레이아웃 분석 및 pdfplumber 심층 테스트
- 블록별 x좌표 분석으로 컬럼 구조 파악
- 섹션 경계 분리 문제 확인
"""

import fitz
import pdfplumber
import os
import re
import sys
from collections import defaultdict

sys.stdout.reconfigure(encoding='utf-8')

BASE_PATH = "../source/2024 Building Code Compendium"
PDF_FILE = "301880.pdf"

def get_pdf_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(script_dir, BASE_PATH, PDF_FILE))


def analyze_column_structure_pymupdf(pdf_path, page_num):
    """PyMuPDF로 컬럼 구조 분석"""
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]
    blocks = page.get_text("blocks")

    page_width = page.rect.width
    page_height = page.rect.height

    # 헤더/풋터 제외
    filtered = [b for b in blocks if b[6] == 0 and b[1] > 60 and b[3] < (page_height - 60)]

    # x좌표 분포 분석
    x_coords = [b[0] for b in filtered]

    # 컬럼 중앙 추정 (페이지 반 기준)
    mid_x = page_width / 2

    left_blocks = [b for b in filtered if b[0] < mid_x - 20]
    right_blocks = [b for b in filtered if b[0] >= mid_x - 20]

    doc.close()

    return {
        'page_width': page_width,
        'mid_x': mid_x,
        'left_count': len(left_blocks),
        'right_count': len(right_blocks),
        'x_coords': sorted(set([round(x, 0) for x in x_coords])),
        'left_blocks': left_blocks,
        'right_blocks': right_blocks
    }


def analyze_with_pdfplumber_chars(pdf_path, page_num):
    """pdfplumber의 chars 레벨 분석"""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num - 1]

        # 헤더/풋터 제외
        cropped = page.crop((0, 60, page.width, page.height - 60))

        chars = cropped.chars

        # x좌표 분포
        x_coords = [c['x0'] for c in chars]

        # 컬럼 추정
        mid_x = page.width / 2

        return {
            'page_width': page.width,
            'char_count': len(chars),
            'x_min': min(x_coords) if x_coords else 0,
            'x_max': max(x_coords) if x_coords else 0,
            'mid_x': mid_x
        }


def extract_text_by_column_pymupdf(pdf_path, page_num):
    """컬럼별로 분리해서 텍스트 추출 (PyMuPDF)"""
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]
    blocks = page.get_text("blocks")

    page_width = page.rect.width
    page_height = page.rect.height
    mid_x = page_width / 2

    # 헤더/풋터 제외
    filtered = [b for b in blocks if b[6] == 0 and b[1] > 60 and b[3] < (page_height - 60)]

    # 컬럼 분리
    left = [b for b in filtered if b[0] < mid_x - 20]
    right = [b for b in filtered if b[0] >= mid_x - 20]

    # 각 컬럼 내에서 y좌표로 정렬
    left.sort(key=lambda b: b[1])
    right.sort(key=lambda b: b[1])

    left_text = '\n'.join([b[4].strip().replace('\n', ' ') for b in left])
    right_text = '\n'.join([b[4].strip().replace('\n', ' ') for b in right])

    # 왼쪽 먼저, 오른쪽 나중 (reading order)
    combined = left_text + '\n--- COLUMN BREAK ---\n' + right_text

    doc.close()
    return combined, left_text, right_text


def check_section_92_93_boundary(pdf_path):
    """9.2와 9.3 섹션 경계 확인"""
    print("\n" + "=" * 70)
    print("🔍 섹션 9.2 / 9.3 경계 분석")
    print("=" * 70)

    # 페이지 716이 9.2와 9.3이 시작하는 곳
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[715]  # 0-indexed, 페이지 716

        text = page.extract_text(layout=True)

        # 9.2와 9.3 위치 찾기
        pos_92 = text.find("9.2.1.")
        pos_93 = text.find("9.3.1.")

        print(f"\n페이지 716 내 위치:")
        print(f"  9.2.1. 위치: {pos_92}")
        print(f"  9.3.1. 위치: {pos_93}")

        if pos_92 > 0 and pos_93 > 0:
            print(f"\n9.2 ~ 9.3 사이 텍스트 ({pos_93 - pos_92}자):")
            between = text[pos_92:pos_93]
            print("-" * 40)
            print(between[:500] + "..." if len(between) > 500 else between)
            print("-" * 40)

            # 9.2 내용이 맞는지 확인
            if "Defined Words" in between or "Words in italics" in between:
                print("✅ 9.2 Definitions 내용이 올바르게 위치함")
            else:
                print("❌ 9.2 내용이 예상과 다름")


def main():
    pdf_path = get_pdf_path()
    print(f"PDF 경로: {pdf_path}")

    # 1. 컬럼 구조 분석
    print("\n" + "=" * 70)
    print("📊 컬럼 구조 분석 (페이지 716-718)")
    print("=" * 70)

    for page_num in [716, 717, 718]:
        print(f"\n--- 페이지 {page_num} ---")

        result = analyze_column_structure_pymupdf(pdf_path, page_num)
        print(f"페이지 너비: {result['page_width']:.0f}px")
        print(f"중앙 x좌표: {result['mid_x']:.0f}px")
        print(f"왼쪽 블록: {result['left_count']}개")
        print(f"오른쪽 블록: {result['right_count']}개")
        print(f"x좌표 분포: {result['x_coords'][:10]}...")

        # 2-column 여부 판단
        if result['right_count'] > 5:
            print("⚠️ 2-column 레이아웃으로 추정")
        else:
            print("📄 단일 컬럼으로 추정")

    # 2. 컬럼별 텍스트 추출 테스트
    print("\n" + "=" * 70)
    print("📝 컬럼별 텍스트 추출 (페이지 717)")
    print("=" * 70)

    combined, left, right = extract_text_by_column_pymupdf(pdf_path, 717)

    print("\n왼쪽 컬럼 (처음 300자):")
    print("-" * 40)
    print(left[:300])

    print("\n오른쪽 컬럼 (처음 300자):")
    print("-" * 40)
    print(right[:300])

    # 3. 섹션 경계 확인
    check_section_92_93_boundary(pdf_path)

    # 4. pdfplumber 테이블 상세
    print("\n" + "=" * 70)
    print("📋 pdfplumber 테이블 추출 상세 (페이지 718)")
    print("=" * 70)

    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[717]  # 페이지 718
        tables = page.extract_tables()

        if tables:
            for i, table in enumerate(tables):
                print(f"\n테이블 {i+1}:")
                for j, row in enumerate(table[:5]):  # 처음 5행만
                    print(f"  행 {j}: {row}")
                if len(table) > 5:
                    print(f"  ... ({len(table) - 5}행 더 있음)")

    print("\n" + "=" * 70)
    print("분석 완료")
    print("=" * 70)


if __name__ == "__main__":
    main()
