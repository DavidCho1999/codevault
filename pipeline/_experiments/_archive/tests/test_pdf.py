"""
OBC PDF 구조 테스트 스크립트
- PDF 열기 확인
- 목차(TOC) 추출
- Part 9 위치 확인
"""

import fitz  # PyMuPDF
import os
import sys

# UTF-8 출력 설정
sys.stdout.reconfigure(encoding='utf-8')

# PDF 경로
BASE_PATH = "../../source/2024 Building Code Compendium"

def analyze_pdf(filename):
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.normpath(os.path.join(script_dir, BASE_PATH, filename))

    print(f"\n{'='*60}")
    print(f"파일: {filename}")
    print(f"경로: {pdf_path}")
    print(f"파일 존재: {os.path.exists(pdf_path)}")

    if not os.path.exists(pdf_path):
        print("PDF 파일을 찾을 수 없습니다!")
        return

    doc = fitz.open(pdf_path)
    print(f"총 페이지 수: {len(doc)}")

    # 목차(TOC) 추출
    toc = doc.get_toc()
    print(f"\n--- 목차 (처음 30개) ---")
    for i, item in enumerate(toc[:30]):
        level, title, page = item
        indent = "  " * (level - 1)
        # 특수문자 제거
        title_clean = title.replace('\u2003', ' ').replace('\u2002', ' ')
        print(f"{indent}[p.{page}] {title_clean}")

    # Part 9 찾기
    print(f"\n--- Part 9 관련 항목 ---")
    part9_items = []
    for item in toc:
        level, title, page = item
        if "Part 9" in title or "PART 9" in title or title.startswith("9.") or "Section 9" in title:
            title_clean = title.replace('\u2003', ' ').replace('\u2002', ' ')
            part9_items.append((level, page, title_clean))
            print(f"[Level {level}] Page {page}: {title_clean}")

    if not part9_items:
        print("Part 9 관련 항목이 없습니다.")

    doc.close()

def main():
    # 두 PDF 모두 분석
    analyze_pdf("301880.pdf")
    analyze_pdf("301881.pdf")
    print("\n완료!")

if __name__ == "__main__":
    main()
