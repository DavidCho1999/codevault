"""PDF에서 실제 테이블 내용 확인"""
import sys
import pdfplumber
sys.stdout.reconfigure(encoding='utf-8')

PDF_PATH = '../source/2024 Building Code Compendium/301880.pdf'

def verify_table_9_23_3_1():
    """Table 9.23.3.1 (Wire Nails) 실제 내용 확인"""
    print("="*60)
    print("Table 9.23.3.1 - Page 866 (index 865)")
    print("="*60)

    with pdfplumber.open(PDF_PATH) as pdf:
        page = pdf.pages[865]

        # 전체 텍스트에서 Table 9.23.3.1 찾기
        text = page.extract_text()
        print("\n[페이지 텍스트에서 테이블 관련 부분]")

        lines = text.split('\n')
        in_table = False
        for line in lines:
            if 'Table 9.23.3.1' in line or 'Wire Nail' in line or 'Minimum Length' in line:
                in_table = True
            if in_table:
                print(f"  {line}")
            if in_table and line.strip() == '':
                in_table = False

        # 테이블 추출
        print("\n[추출된 테이블]")
        tables = page.extract_tables()
        for i, table in enumerate(tables):
            print(f"\nTable {i}:")
            for row in table:
                print(f"  {row}")


if __name__ == "__main__":
    verify_table_9_23_3_1()
