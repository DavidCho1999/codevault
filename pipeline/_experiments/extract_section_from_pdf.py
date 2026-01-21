"""
PDF에서 특정 섹션의 텍스트를 추출하는 스크립트
Usage: python extract_section_from_pdf.py 9.8
"""
import fitz
import sys
import json

def find_section_page(doc, section_id, index_path='codevault/public/data/part9-index.json'):
    """섹션 시작 페이지 찾기 (인덱스 파일 사용)"""
    try:
        # 인덱스에서 페이지 번호 가져오기
        with open(index_path, 'r', encoding='utf-8') as f:
            index = json.load(f)

        # section_id에 해당하는 첫 subsection 찾기 (예: 9.8 -> 9.8.1)
        for item in index:
            if item.get('sectionId') == section_id:
                page = item.get('page')
                if page:
                    return page - 1  # 0-indexed로 변환

        # 인덱스에 없으면 PDF에서 직접 검색
        for page_num in range(700, min(len(doc), 900)):
            text = doc[page_num].get_text()
            if 'Part 9' in text and f'Section {section_id}' in text:
                return page_num

        return None
    except Exception as e:
        print(f"Warning: {e}", file=sys.stderr)
        return None

def extract_section_text(pdf_path, section_id, max_pages=20):
    """섹션의 텍스트 추출 (최대 max_pages 페이지)"""
    try:
        doc = fitz.open(pdf_path)

        # 섹션 시작 페이지 찾기
        start_page = find_section_page(doc, section_id)
        if start_page is None:
            return {"error": f"Section {section_id} not found in PDF"}

        # 섹션 텍스트 추출
        section_text = []
        for i in range(max_pages):
            page_num = start_page + i
            if page_num >= len(doc):
                break

            text = doc[page_num].get_text()
            section_text.append(text)

            # 다음 주요 섹션 시작하면 중단
            # (예: 9.8 다음은 9.9)
            next_section = f"{float(section_id) + 0.1:.1f}."
            if i > 0 and next_section in text:
                break

        full_text = '\n'.join(section_text)

        # 첫 500자 반환
        preview = full_text[:800]

        return {
            "section_id": section_id,
            "start_page": start_page + 1,  # 1-indexed
            "pages_extracted": len(section_text),
            "total_chars": len(full_text),
            "preview": preview
        }

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    # UTF-8 출력 설정
    sys.stdout.reconfigure(encoding='utf-8')

    if len(sys.argv) < 2:
        print("Usage: python extract_section_from_pdf.py <section_id>")
        print("Example: python extract_section_from_pdf.py 9.8")
        sys.exit(1)

    section_id = sys.argv[1]
    pdf_path = "source/2024 Building Code Compendium/301880.pdf"

    result = extract_section_text(pdf_path, section_id)

    # JSON으로 출력
    print(json.dumps(result, ensure_ascii=False, indent=2))
