"""
PyMuPDF vs pdfplumber 비교 테스트
- 문제 섹션: 9.2 (Definitions), 9.3 (Materials)
- 페이지: 716~718
- 비교 항목: 텍스트 순서, 섹션 경계, 테이블 추출
"""

import fitz  # PyMuPDF
import pdfplumber
import os
import re
import sys

sys.stdout.reconfigure(encoding='utf-8')

# 경로 설정
BASE_PATH = "../source/2024 Building Code Compendium"
PDF_FILE = "301880.pdf"

def get_pdf_path():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.normpath(os.path.join(script_dir, BASE_PATH, PDF_FILE))


def extract_with_pymupdf(pdf_path, page_num):
    """PyMuPDF로 텍스트 추출 (현재 방식)"""
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]

    # 블록 기반 추출
    blocks = page.get_text("blocks")
    page_height = page.rect.height

    # 헤더/풋터 제외 (상단 60px, 하단 60px)
    filtered = [b for b in blocks if b[6] == 0 and b[1] > 60 and b[3] < (page_height - 60)]

    # y → x 정렬
    filtered.sort(key=lambda b: (b[1], b[0]))

    lines = []
    for b in filtered:
        text = b[4].strip().replace('\n', ' ')
        if text and not re.match(r'^\d{1,3}$', text):  # 페이지 번호 제외
            lines.append(text)

    doc.close()
    return '\n'.join(lines)


def extract_with_pdfplumber(pdf_path, page_num):
    """pdfplumber로 텍스트 추출 (layout=True)"""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num - 1]

        # 헤더/풋터 제외
        cropped = page.crop((0, 60, page.width, page.height - 60))

        # layout=True: 시각적 레이아웃 보존
        text = cropped.extract_text(layout=True)

        if text:
            # 페이지 번호 제거
            lines = [l for l in text.split('\n') if not re.match(r'^\s*\d{1,3}\s*$', l)]
            return '\n'.join(lines)
        return ""


def extract_tables_with_pdfplumber(pdf_path, page_num):
    """pdfplumber로 테이블 추출"""
    with pdfplumber.open(pdf_path) as pdf:
        page = pdf.pages[page_num - 1]
        tables = page.extract_tables()
        return tables


def find_section_ids(text):
    """텍스트에서 섹션 ID 추출 (순서 확인용)"""
    pattern = r'9\.\d+\.\d+\.\d+\.'
    return re.findall(pattern, text)


def check_section_order(section_ids):
    """섹션 ID 순서가 올바른지 확인"""
    if len(section_ids) < 2:
        return True, []

    issues = []
    for i in range(len(section_ids) - 1):
        curr = section_ids[i]
        next_id = section_ids[i + 1]

        # 숫자 추출해서 비교
        curr_nums = [int(x) for x in curr.rstrip('.').split('.')]
        next_nums = [int(x) for x in next_id.rstrip('.').split('.')]

        # 간단한 순서 체크 (같은 subsection 내에서)
        if curr_nums[:3] == next_nums[:3]:  # 같은 9.x.x. 내에서
            if curr_nums[3] > next_nums[3]:
                issues.append(f"순서 오류: {curr} > {next_id}")

    return len(issues) == 0, issues


def main():
    pdf_path = get_pdf_path()
    print(f"PDF 경로: {pdf_path}")
    print("=" * 70)

    # 테스트 페이지: 716 (9.2, 9.3 시작), 717, 718 (테이블 포함)
    test_pages = [716, 717, 718]

    for page_num in test_pages:
        print(f"\n{'='*70}")
        print(f"📄 페이지 {page_num} 비교")
        print("=" * 70)

        # 1. PyMuPDF 추출
        pymupdf_text = extract_with_pymupdf(pdf_path, page_num)
        pymupdf_ids = find_section_ids(pymupdf_text)
        pymupdf_order_ok, pymupdf_issues = check_section_order(pymupdf_ids)

        # 2. pdfplumber 추출
        pdfplumber_text = extract_with_pdfplumber(pdf_path, page_num)
        pdfplumber_ids = find_section_ids(pdfplumber_text)
        pdfplumber_order_ok, pdfplumber_issues = check_section_order(pdfplumber_ids)

        # 3. 테이블 추출 (pdfplumber만)
        tables = extract_tables_with_pdfplumber(pdf_path, page_num)

        # 결과 출력
        print(f"\n📊 섹션 ID 순서 비교")
        print("-" * 40)
        print(f"PyMuPDF 발견 섹션 IDs ({len(pymupdf_ids)}개):")
        print(f"  {pymupdf_ids[:10]}{'...' if len(pymupdf_ids) > 10 else ''}")
        print(f"  순서 정상: {'✅' if pymupdf_order_ok else '❌'}")
        if pymupdf_issues:
            for issue in pymupdf_issues[:3]:
                print(f"    - {issue}")

        print(f"\npdfplumber 발견 섹션 IDs ({len(pdfplumber_ids)}개):")
        print(f"  {pdfplumber_ids[:10]}{'...' if len(pdfplumber_ids) > 10 else ''}")
        print(f"  순서 정상: {'✅' if pdfplumber_order_ok else '❌'}")
        if pdfplumber_issues:
            for issue in pdfplumber_issues[:3]:
                print(f"    - {issue}")

        # 텍스트 미리보기
        print(f"\n📝 텍스트 미리보기 (처음 500자)")
        print("-" * 40)
        print("PyMuPDF:")
        print(pymupdf_text[:500])
        print("\n" + "-" * 40)
        print("pdfplumber:")
        print(pdfplumber_text[:500])

        # 테이블 정보
        if tables:
            print(f"\n📋 테이블 발견: {len(tables)}개")
            for i, table in enumerate(tables):
                if table:
                    print(f"  테이블 {i+1}: {len(table)}행 x {len(table[0]) if table else 0}열")
                    if table and len(table) > 0:
                        print(f"    헤더: {table[0][:3]}...")

    # 전체 요약
    print("\n" + "=" * 70)
    print("📊 전체 요약")
    print("=" * 70)

    print("""
비교 결과를 확인해주세요:
1. 섹션 ID 순서가 올바른가? (9.3.1.1 → 9.3.1.2 → ...)
2. 텍스트 레이아웃이 논리적인가?
3. 테이블이 제대로 인식되는가?

다음 단계:
- pdfplumber가 더 나으면 → 파싱 스크립트 전환
- 비슷하면 → 추가 개선 필요 (column 감지 등)
""")


if __name__ == "__main__":
    main()
