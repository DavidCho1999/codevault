#!/usr/bin/env python3
"""
Vision API Table Extraction Test
- PDF 페이지 이미지 -> Claude Vision API -> 테이블 JSON
- 좌표 기반 추출 대신 시각적 이해 기반
"""

import anthropic
import base64
import json
import fitz
from pathlib import Path

def extract_page_as_image(pdf_path: str, page_num: int, zoom: float = 2.0) -> bytes:
    """PDF 페이지를 이미지로 변환하여 bytes 반환"""
    doc = fitz.open(pdf_path)
    page = doc[page_num - 1]  # 1-indexed to 0-indexed

    mat = fitz.Matrix(zoom, zoom)
    pix = page.get_pixmap(matrix=mat)

    img_bytes = pix.tobytes("png")
    doc.close()

    return img_bytes


def extract_table_with_vision(image_bytes: bytes, table_id: str) -> dict:
    """Claude Vision API로 테이블 추출"""
    client = anthropic.Anthropic()

    # Base64 인코딩
    image_data = base64.standard_b64encode(image_bytes).decode("utf-8")

    prompt = f"""이 PDF 페이지 이미지에서 Table {table_id}를 찾아 정확하게 추출해주세요.

다음 JSON 형식으로 반환해주세요:
{{
  "table_id": "{table_id}",
  "title": "테이블 제목",
  "header_rows": 헤더 행 개수,
  "data": [
    ["Row 0 Cell 0", "Row 0 Cell 1", ...],
    ["Row 1 Cell 0", "Row 1 Cell 1", ...],
    ...
  ],
  "spans": {{
    "rowspans": [{{"row": 0, "col": 0, "span": 2}}, ...],
    "colspans": [{{"row": 0, "col": 1, "span": 3}}, ...]
  }},
  "notes": "테이블 아래 Notes가 있으면 여기에"
}}

중요 규칙:
1. 셀 병합(colspan/rowspan)이 있으면 spans에 명시
2. 병합된 셀의 다른 위치는 data에서 null로 표시
3. 특수 기호(>=, <=, 분수 등)는 그대로 유지
4. 각주 번호(1), (2) 등은 포함
5. JSON만 반환 (다른 설명 없이)"""

    message = client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=4096,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": "image/png",
                            "data": image_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ],
            }
        ],
    )

    # 응답에서 JSON 추출
    response_text = message.content[0].text

    # JSON 부분만 파싱
    try:
        # JSON 블록 찾기
        if "```json" in response_text:
            json_str = response_text.split("```json")[1].split("```")[0].strip()
        elif "```" in response_text:
            json_str = response_text.split("```")[1].split("```")[0].strip()
        else:
            json_str = response_text.strip()

        result = json.loads(json_str)
        return result
    except json.JSONDecodeError as e:
        print(f"JSON 파싱 실패: {e}")
        print(f"원본 응답:\n{response_text}")
        return {"error": str(e), "raw_response": response_text}


def test_table_extraction(table_id: str, page_num: int):
    """테이블 추출 테스트"""
    pdf_path = Path(__file__).parent.parent / "source" / "2024 Building Code Compendium" / "301880.pdf"

    print("=" * 60)
    print(f"VISION API TABLE EXTRACTION TEST")
    print(f"Table: {table_id}, Page: {page_num}")
    print("=" * 60)

    # 1. 이미지 추출
    print("\n[1] Extracting page as image...")
    image_bytes = extract_page_as_image(str(pdf_path), page_num)
    print(f"    Image size: {len(image_bytes)} bytes")

    # 2. Vision API 호출
    print("\n[2] Calling Claude Vision API...")
    result = extract_table_with_vision(image_bytes, table_id)

    # 3. 결과 출력
    print("\n[3] RESULT:")
    print("-" * 40)
    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 4. 결과 저장
    output_path = Path(__file__).parent / f"vision_result_{table_id.replace('.', '_')}.json"
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    print(f"\n[4] Result saved to: {output_path}")

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) >= 3:
        table_id = sys.argv[1]
        page_num = int(sys.argv[2])
    else:
        # 기본값: Table 9.3.1.7, page 718
        table_id = "9.3.1.7"
        page_num = 718

    test_table_extraction(table_id, page_num)
