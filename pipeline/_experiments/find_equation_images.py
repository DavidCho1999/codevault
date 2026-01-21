"""
수식 이미지 스캔 스크립트
- PDF에서 이미지로 저장된 수식 찾기
- "calculated as follows", "formula" 등 앞에 이미지가 있으면 수식일 가능성 높음
"""

import fitz
import sys
from pathlib import Path

# 설정
PDF_PATH = Path(__file__).parent.parent / "source/2024 Building Code Compendium/301880.pdf"
PART9_START = 715  # Part 9 시작 페이지 (0-indexed)
PART9_END = 990    # Part 9 끝 페이지

# 수식 전조 키워드
EQUATION_KEYWORDS = [
    'calculated as follows',
    'determined by',
    'using the formula',
    'shall be calculated',
    'equal to',
    'computed as',
]


def find_equation_images():
    """PDF에서 수식 이미지 찾기"""

    if not PDF_PATH.exists():
        print(f"ERROR: PDF not found at {PDF_PATH}")
        return []

    doc = fitz.open(str(PDF_PATH))
    results = []

    print(f"Scanning Part 9 (pages {PART9_START+1} to {PART9_END})...\n")

    for page_num in range(PART9_START, min(PART9_END, len(doc))):
        page = doc[page_num]
        blocks = page.get_text("dict")["blocks"]

        # 텍스트 라인 수집
        text_lines = []
        for block in blocks:
            if block["type"] == 0:  # text
                for line in block.get("lines", []):
                    y = line["bbox"][1]
                    text = "".join([span["text"] for span in line["spans"]])
                    text_lines.append((y, text))

        # 이미지 블록 확인
        for block in blocks:
            if block["type"] == 1:  # image
                bbox = block["bbox"]
                y = bbox[1]
                width = bbox[2] - bbox[0]
                height = bbox[3] - bbox[1]

                # 헤더 제외 (y > 50), 수식 크기 범위
                if y > 50 and 30 < width < 400 and 15 < height < 120:
                    # 이미지 앞 텍스트 찾기
                    before_text = ""
                    for ty, text in sorted(text_lines):
                        if ty < y - 5:
                            before_text = text

                    # 수식 키워드 체크
                    is_equation = any(kw in before_text.lower() for kw in EQUATION_KEYWORDS)

                    if is_equation:
                        results.append({
                            'page': page_num + 1,
                            'size': f'{width:.0f}x{height:.0f}',
                            'y': y,
                            'before': before_text[:80],
                            'keyword_matched': True
                        })
                    elif width > 60 and height > 25:
                        # 키워드 없어도 수식 크기면 의심
                        results.append({
                            'page': page_num + 1,
                            'size': f'{width:.0f}x{height:.0f}',
                            'y': y,
                            'before': before_text[:80] if before_text else "(no text before)",
                            'keyword_matched': False
                        })

    doc.close()
    return results


def main():
    print("=" * 60)
    print("  수식 이미지 스캔 (Part 9)")
    print("=" * 60)

    results = find_equation_images()

    # 키워드 매칭된 것 (높은 확률)
    matched = [r for r in results if r['keyword_matched']]
    # 의심되는 것
    suspected = [r for r in results if not r['keyword_matched']]

    print(f"\n## 확실한 수식 이미지 ({len(matched)}개)")
    print("-" * 60)
    for r in matched:
        print(f"Page {r['page']} ({r['size']}):")
        print(f"  Context: {r['before']}")
        print()

    if not matched:
        print("  없음\n")

    print(f"\n## 의심되는 이미지 ({len(suspected)}개)")
    print("-" * 60)
    for r in suspected[:10]:  # 상위 10개만
        print(f"Page {r['page']} ({r['size']}): {r['before'][:50]}")

    if len(suspected) > 10:
        print(f"  ... and {len(suspected) - 10} more")

    if not suspected:
        print("  없음\n")

    print("\n" + "=" * 60)
    print(f"  총 {len(matched)}개 수식 이미지 발견 (확실)")
    print(f"  총 {len(suspected)}개 의심 이미지")
    print("=" * 60)

    return len(matched)


if __name__ == "__main__":
    sys.exit(0 if main() == 0 else 1)
