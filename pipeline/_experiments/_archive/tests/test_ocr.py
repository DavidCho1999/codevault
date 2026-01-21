"""
이미지 OCR 테스트 - EasyOCR
PDF 테이블 영역을 이미지로 변환 후 OCR
"""
import sys
import fitz
import os
from PIL import Image
import io

sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'
OUTPUT_DIR = './extraction_test_results'

def pdf_page_to_image(doc, page_num, dpi=300):
    """PDF 페이지를 이미지로 변환"""
    page = doc[page_num]
    mat = fitz.Matrix(dpi/72, dpi/72)
    pix = page.get_pixmap(matrix=mat)
    img_data = pix.tobytes("png")
    return Image.open(io.BytesIO(img_data))


def extract_table_region(doc, page_num, table_index=0):
    """테이블 영역만 이미지로 추출"""
    page = doc[page_num]
    tabs = page.find_tables()

    if not tabs.tables or table_index >= len(tabs.tables):
        return None

    tab = tabs.tables[table_index]
    bbox = tab.bbox  # (x0, y0, x1, y1)

    # 여유 추가
    margin = 10
    clip_rect = fitz.Rect(
        bbox[0] - margin,
        bbox[1] - margin,
        bbox[2] + margin,
        bbox[3] + margin
    )

    # 고해상도 렌더링
    mat = fitz.Matrix(3, 3)  # 3x 확대
    pix = page.get_pixmap(matrix=mat, clip=clip_rect)
    img_data = pix.tobytes("png")
    return Image.open(io.BytesIO(img_data))


def test_easyocr():
    """EasyOCR 테스트"""
    print("="*60)
    print("EasyOCR 테스트")
    print("="*60)

    try:
        import easyocr
        print("EasyOCR 로딩 중... (최초 실행 시 모델 다운로드)")
        reader = easyocr.Reader(['en'], gpu=False)
        print("EasyOCR 준비 완료")
    except Exception as e:
        print(f"EasyOCR 로딩 실패: {e}")
        return

    doc = fitz.open(PDF_PATH)

    # 간단한 테이블로 테스트 (Table 9.23.3.1)
    test_cases = [
        {'name': 'Table 9.23.3.1', 'page': 865, 'table_index': 0},
    ]

    os.makedirs(OUTPUT_DIR, exist_ok=True)

    for tc in test_cases:
        print(f"\n[{tc['name']}]")

        # 테이블 영역 이미지 추출
        img = extract_table_region(doc, tc['page'], tc['table_index'])

        if img is None:
            print("  테이블 영역 추출 실패")
            continue

        # 이미지 저장 (확인용)
        img_path = f"{OUTPUT_DIR}/{tc['name'].replace(' ', '_')}_region.png"
        img.save(img_path)
        print(f"  이미지 저장: {img_path}")

        # OCR 수행
        print("  OCR 수행 중...")
        results = reader.readtext(img_path)

        print(f"  인식된 텍스트 수: {len(results)}")
        for i, (bbox, text, conf) in enumerate(results[:10]):  # 처음 10개만
            print(f"    [{i}] {text} (conf: {conf:.2f})")

    doc.close()


if __name__ == "__main__":
    test_easyocr()
