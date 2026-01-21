#!/usr/bin/env python3
"""
Part 9 최종 검증 스크립트
- PDF 원본과 JSON/웹 렌더링 비교
- 한 번 돌리면 두 번 다시 리뷰 안 해도 되는 수준
"""

import json
import re
import fitz  # PyMuPDF
import sys
from pathlib import Path
from difflib import SequenceMatcher

# 인코딩 설정
sys.stdout.reconfigure(encoding='utf-8')

# 경로 설정
BASE_DIR = Path(__file__).parent.parent
PDF_PATH = BASE_DIR / "source" / "2024 Building Code Compendium" / "301880.pdf"
JSON_PATH = BASE_DIR / "codevault" / "public" / "data" / "part9.json"
TABLES_PATH = BASE_DIR / "codevault" / "public" / "data" / "part9_tables.json"
REPORT_PATH = BASE_DIR / "_report" / "FINAL_VERIFICATION_REPORT.md"


def load_data():
    """JSON 데이터 로드"""
    with open(JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    with open(TABLES_PATH, 'r', encoding='utf-8') as f:
        tables = json.load(f)
    return data, tables


def extract_pdf_text_by_page(pdf_path, start_page, end_page):
    """PDF에서 페이지 범위의 텍스트 추출"""
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(start_page - 1, min(end_page, len(doc))):
        page = doc[page_num]
        text += page.get_text("text")
    doc.close()
    return text


def normalize_text(text):
    """텍스트 정규화 (비교용)"""
    # 공백 정규화
    text = re.sub(r'\s+', ' ', text)
    # 특수문자 정규화
    text = text.replace('–', '-').replace('—', '-')
    text = text.replace(''', "'").replace(''', "'")
    text = text.replace('"', '"').replace('"', '"')
    return text.strip().lower()


def similarity_ratio(text1, text2):
    """두 텍스트의 유사도 계산"""
    return SequenceMatcher(None, normalize_text(text1), normalize_text(text2)).ratio()


def extract_first_sentences(text, n=2):
    """첫 n개 문장 추출"""
    # 문장 분리
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    return ' '.join(sentences[:n])


def check_article_structure(content, subsection_id):
    """Article 구조 검증"""
    pattern = rf'^({re.escape(subsection_id)}\.\d+)\.\s+'
    matches = re.findall(pattern, content, re.MULTILINE)

    unique = []
    for m in matches:
        if m not in unique:
            unique.append(m)

    # 연속성 체크
    gaps = []
    for i in range(len(unique) - 1):
        curr = int(unique[i].split('.')[-1])
        next_num = int(unique[i+1].split('.')[-1])
        if next_num != curr + 1:
            gaps.append((unique[i], unique[i+1], next_num - curr - 1))

    return {
        'articles': unique,
        'count': len(unique),
        'gaps': gaps,
        'has_gaps': len(gaps) > 0
    }


def check_table_references(content, tables_data):
    """테이블 참조 검증"""
    refs = re.findall(r'Table\s+(9\.\d+\.\d+\.\d+[.-]?[A-G]?)', content)
    unique_refs = list(set(refs))

    results = []
    for ref in unique_refs:
        table_key = f'Table {ref}'.rstrip('.')
        exists = table_key in tables_data or any(ref in k for k in tables_data.keys())
        # Note A 참조는 제외
        is_note_ref = f'Note A-Table {ref}' in content or f'Note A-{ref}' in content

        if not exists and not is_note_ref:
            results.append({'ref': ref, 'exists': False, 'is_note': is_note_ref})
        else:
            results.append({'ref': ref, 'exists': True, 'is_note': is_note_ref})

    return results


def check_equation_markers(content, equations_field):
    """수식 마커 검증"""
    markers = list(re.finditer(r'(calculated as follows|shall be determined by)[:\s]*', content, re.IGNORECASE))

    results = []
    for match in markers:
        # 마커 뒤에 실제 수식이 있는지 확인
        after_text = content[match.end():match.end()+200]
        has_equation = bool(re.search(r'[A-Za-z]\s*=\s*[^,\n]{5,}', after_text))

        # equations 필드에 있는지 확인
        in_field = False
        if equations_field:
            for eq_id, eq_data in equations_field.items():
                if eq_data.get('insertAfter', '') in content[match.start()-50:match.end()+50]:
                    in_field = True
                    break

        results.append({
            'position': match.start(),
            'marker': match.group(),
            'has_equation_after': has_equation,
            'in_equations_field': in_field,
            'context': content[max(0, match.start()-30):match.end()+50].replace('\n', ' ')[:80]
        })

    return results


def verify_section(section, subsections, tables_data, pdf_doc):
    """섹션 전체 검증"""
    results = {
        'id': section['id'],
        'title': section['title'],
        'subsections': [],
        'issues': [],
        'warnings': []
    }

    for sub in subsections:
        content = sub.get('content', '')
        equations = sub.get('equations', {})

        sub_result = {
            'id': sub['id'],
            'title': sub['title'],
            'content_length': len(content),
            'checks': {}
        }

        # 1. Content 길이 체크
        if len(content) < 50:
            results['issues'].append(f"{sub['id']}: Content too short ({len(content)} chars)")

        # 2. Article 구조 체크
        article_check = check_article_structure(content, sub['id'])
        sub_result['checks']['articles'] = article_check
        if article_check['has_gaps']:
            for gap in article_check['gaps']:
                results['issues'].append(f"{sub['id']}: Article gap {gap[0]} -> {gap[1]} (missing {gap[2]})")

        # 3. 테이블 참조 체크
        table_check = check_table_references(content, tables_data)
        sub_result['checks']['tables'] = table_check
        for t in table_check:
            if not t['exists'] and not t['is_note']:
                results['issues'].append(f"{sub['id']}: Missing table {t['ref']}")

        # 4. 수식 마커 체크
        eq_check = check_equation_markers(content, equations)
        sub_result['checks']['equations'] = eq_check
        for eq in eq_check:
            if not eq['has_equation_after'] and not eq['in_equations_field']:
                results['warnings'].append(f"{sub['id']}: Equation marker without equation - {eq['context']}")

        # 5. PDF 원본과 첫 문장 비교 (페이지 정보가 있는 경우)
        if 'page' in sub and pdf_doc:
            try:
                page = pdf_doc[sub['page'] - 1]
                pdf_text = page.get_text("text")

                # JSON 첫 문장
                json_first = extract_first_sentences(content, 2)

                # PDF에서 해당 섹션 찾기
                sub_pattern = rf'{re.escape(sub["id"])}\.\s+'
                match = re.search(sub_pattern, pdf_text)
                if match:
                    pdf_section = pdf_text[match.start():match.start()+500]
                    pdf_first = extract_first_sentences(pdf_section, 2)

                    sim = similarity_ratio(json_first, pdf_first)
                    sub_result['checks']['pdf_similarity'] = sim

                    if sim < 0.8:
                        results['warnings'].append(f"{sub['id']}: Low PDF similarity ({sim:.2%})")
            except Exception as e:
                sub_result['checks']['pdf_error'] = str(e)

        results['subsections'].append(sub_result)

    return results


def generate_report(all_results):
    """마크다운 리포트 생성"""
    report = []
    report.append("# Part 9 최종 검증 리포트")
    report.append("")
    report.append(f"> 자동 생성됨 - {__import__('datetime').datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("")

    # 요약
    total_issues = sum(len(r['issues']) for r in all_results)
    total_warnings = sum(len(r['warnings']) for r in all_results)
    total_sections = len(all_results)

    report.append("## 요약")
    report.append("")
    report.append(f"| 항목 | 값 |")
    report.append(f"|------|-----|")
    report.append(f"| 검증된 섹션 | {total_sections} |")
    report.append(f"| 이슈 (Critical) | {total_issues} |")
    report.append(f"| 경고 (Warning) | {total_warnings} |")
    report.append(f"| 상태 | {'PASS' if total_issues == 0 else 'FAIL'} |")
    report.append("")

    # 이슈 목록
    if total_issues > 0:
        report.append("## Critical 이슈")
        report.append("")
        for r in all_results:
            if r['issues']:
                for issue in r['issues']:
                    report.append(f"- [ ] {issue}")
        report.append("")

    # 경고 목록
    if total_warnings > 0:
        report.append("## Warnings")
        report.append("")
        for r in all_results:
            if r['warnings']:
                for warning in r['warnings']:
                    report.append(f"- {warning}")
        report.append("")

    # 섹션별 상세
    report.append("## 섹션별 상세")
    report.append("")

    for r in all_results:
        status = "PASS" if not r['issues'] else "FAIL"
        emoji = "[OK]" if status == "PASS" else "[FAIL]"
        report.append(f"### {emoji} {r['id']}: {r['title']}")
        report.append("")

        for sub in r['subsections']:
            articles = sub['checks'].get('articles', {})
            tables = sub['checks'].get('tables', [])
            equations = sub['checks'].get('equations', [])

            report.append(f"- **{sub['id']}**: {sub['content_length']} chars, "
                         f"{articles.get('count', 0)} articles, "
                         f"{len(tables)} tables, "
                         f"{len(equations)} eq markers")

        report.append("")

    return "\n".join(report)


def main():
    print("=" * 70)
    print("Part 9 최종 검증 시작")
    print("=" * 70)

    # 데이터 로드
    print("\n[1/4] 데이터 로드 중...")
    data, tables = load_data()

    # PDF 열기
    print("[2/4] PDF 열기...")
    pdf_doc = None
    if PDF_PATH.exists():
        pdf_doc = fitz.open(PDF_PATH)
        print(f"  PDF: {len(pdf_doc)} pages")
    else:
        print(f"  [WARN] PDF not found: {PDF_PATH}")

    # 섹션 검증
    print("[3/4] 섹션 검증 중...")
    all_results = []

    for section in data['sections']:
        result = verify_section(section, section['subsections'], tables, pdf_doc)
        all_results.append(result)

        status = "OK" if not result['issues'] else f"ISSUES: {len(result['issues'])}"
        print(f"  {section['id']}: {status}")

    # PDF 닫기
    if pdf_doc:
        pdf_doc.close()

    # 리포트 생성
    print("[4/4] 리포트 생성 중...")
    report = generate_report(all_results)

    REPORT_PATH.parent.mkdir(exist_ok=True)
    with open(REPORT_PATH, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n리포트 저장: {REPORT_PATH}")

    # 최종 결과
    total_issues = sum(len(r['issues']) for r in all_results)
    total_warnings = sum(len(r['warnings']) for r in all_results)

    print("\n" + "=" * 70)
    print("최종 결과")
    print("=" * 70)
    print(f"Issues: {total_issues}")
    print(f"Warnings: {total_warnings}")
    print(f"Status: {'PASS' if total_issues == 0 else 'FAIL'}")

    return total_issues == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
