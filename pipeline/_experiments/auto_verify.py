"""
Part 9 Auto Verification Script
- No token usage, pure Python verification
- PASS: Auto pass (no manual verification needed)
- FAIL: /verify manual verification required

Usage:
  python auto_verify.py              # JSON 검증만
  python auto_verify.py --web        # JSON + 웹 렌더링 검증
  python auto_verify.py --web 9.8    # 특정 섹션만 웹 검증
"""

import json
import re
import sys
import io
import argparse
from pathlib import Path
from urllib.request import urlopen
from urllib.error import URLError

# Fix Windows encoding
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

# 파일 경로
BASE_DIR = Path(__file__).parent.parent
SECTIONS_FILE = BASE_DIR / "codevault/public/data/part9.json"
TABLES_FILE = BASE_DIR / "codevault/public/data/part9_tables.json"


def load_data():
    """JSON 데이터 로드"""
    with open(SECTIONS_FILE, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # part9.json 구조: { "id": "9", "sections": [...] }
    sections = data.get('sections', [])

    tables = {}
    if TABLES_FILE.exists():
        with open(TABLES_FILE, 'r', encoding='utf-8') as f:
            tables = json.load(f)

    return sections, tables


def check_content_length(content, min_length=200):
    """Content 길이 체크"""
    if not content:
        return False, "content 비어있음"
    if len(content) < min_length:
        return False, f"content 짧음 ({len(content)}자)"
    return True, None


def check_sentence_separation(content):
    """소문자로 시작하는 별도 줄 체크 (문장 분리 오류)"""
    # 예: "as specified in Sentence (1)." 가 별도 줄로 분리됨
    separated = re.findall(r'\n([a-z][^\n]{10,60})', content)

    # 허용되는 패턴 제외 (예: "and", "or" 로 시작하는 리스트)
    false_positives = ['and ', 'or ', 'the ', 'a ']
    filtered = [s for s in separated if not any(s.startswith(fp) for fp in false_positives)]

    if filtered:
        return False, f"문장 분리 의심: '{filtered[0][:40]}...'"
    return True, None


def check_clause_newlines(content):
    """(a), (b), (c) clause 앞에 줄바꿈 있는지"""
    # (a)가 있는데 \n(a)가 없으면 문제
    for clause in ['(a)', '(b)', '(c)']:
        if clause in content:
            # 줄 시작에 있거나, 콜론 뒤에 있거나, \n 뒤에 있어야 함
            pattern = rf'(?:^|\n|:\s*){re.escape(clause)}'
            if not re.search(pattern, content, re.MULTILINE):
                # 문장 중간에 있는 참조 clause는 OK (예: "see clause (a)")
                ref_pattern = rf'(?:see|in|under|per)\s+{re.escape(clause)}'
                if not re.search(ref_pattern, content, re.IGNORECASE):
                    return False, f"{clause} 앞에 줄바꿈 없음"
    return True, None


def check_equations(content, section_id):
    """수식이 필요한 섹션에서 수식 존재 확인"""
    # 수식이 필요한 섹션
    equation_sections = ['9.4.2', '9.8', '9.25']

    needs_equation = any(section_id.startswith(es) for es in equation_sections)
    if not needs_equation:
        return True, "N/A"

    # 수식 패턴 체크
    equation_patterns = [
        r'[A-Za-z]+\s*=\s*[\d\w\s\+\-\*\/\(\)]+',  # x = ... 형식
        r'≤|≥|×|÷|√',  # 수학 기호
    ]

    has_equation = any(re.search(p, content) for p in equation_patterns)

    if not has_equation:
        # "shall be calculated" 있으면 수식 필요
        if 'shall be calculated' in content.lower():
            return False, "수식 누락 의심 (calculated 있는데 수식 없음)"

    return True, None


def check_subsections(section_data):
    """Subsection 존재 확인"""
    subsections = section_data.get('subsections', [])
    if not subsections:
        # 일부 섹션은 subsection 없을 수 있음 (9.2 Definitions 등)
        return True, "subsection 없음 (정상일 수 있음)"
    return True, None


def check_web_rendering(section_id, base_url="http://localhost:3001"):
    """웹 렌더링 검증 (Playwright 대체)"""
    url = f"{base_url}/code/{section_id}"

    try:
        with urlopen(url, timeout=5) as response:
            html = response.read().decode('utf-8')
    except URLError as e:
        return False, f"서버 연결 실패: {e}"
    except Exception as e:
        return False, f"요청 실패: {e}"

    results = []

    # 1. 에러 페이지 체크
    if 'error' in html.lower() and 'class="error' in html.lower():
        results.append("[FAIL] 에러 페이지 감지")

    # 2. 섹션 제목 존재
    if f'>{section_id}' not in html and f'Section {section_id}' not in html:
        results.append("[WARN] 섹션 제목 없음")

    # 3. Content 존재 (최소한의 텍스트)
    # <main> 또는 content 영역에 텍스트가 있는지
    if len(html) < 5000:
        results.append("[WARN] HTML 짧음 (content 부족 의심)")

    # 4. 테이블 버튼 존재 (테이블이 있는 섹션)
    table_sections = ['9.3', '9.4', '9.7', '9.8', '9.9', '9.10', '9.20', '9.23', '9.25', '9.32', '9.36']
    if any(section_id.startswith(ts) for ts in table_sections):
        if 'Table' not in html:
            results.append("[WARN] 테이블 버튼 없음")

    # 5. 기본 레이아웃 존재
    if '<h1' not in html and '<h2' not in html:
        results.append("[WARN] 헤딩 태그 없음")

    has_fail = any('[FAIL]' in r for r in results)

    if has_fail:
        return False, results
    elif results:
        return True, results  # WARN만 있으면 PASS + 경고
    else:
        return True, ["웹 렌더링 OK"]


def verify_section(section_id, sections_data, tables_data):
    """단일 섹션 검증"""
    results = []

    # 섹션 찾기
    section = None
    for s in sections_data:
        if s.get('id') == section_id:
            section = s
            break

    if not section:
        return "SKIP", ["섹션 없음"]

    # subsections에서 content 모두 합치기
    subsections = section.get('subsections', [])
    content = '\n'.join(sub.get('content', '') for sub in subsections)

    # 체크 1: Content 길이
    ok, msg = check_content_length(content)
    if not ok:
        results.append(f"[FAIL] {msg}")

    # 체크 2: 문장 분리
    ok, msg = check_sentence_separation(content)
    if not ok:
        results.append(f"[WARN] {msg}")

    # 체크 3: Clause 줄바꿈
    ok, msg = check_clause_newlines(content)
    if not ok:
        results.append(f"[WARN] {msg}")

    # 체크 4: 수식
    ok, msg = check_equations(content, section_id)
    if not ok:
        results.append(f"[FAIL] {msg}")
    elif msg == "N/A":
        pass  # 수식 불필요

    # 체크 5: Subsection
    ok, msg = check_subsections(section)
    if not ok:
        results.append(f"[INFO] {msg}")

    # 최종 판정
    has_fail = any('[FAIL]' in r for r in results)
    has_warn = any('[WARN]' in r for r in results)

    if has_fail:
        return "FAIL", results
    elif has_warn:
        return "WARN", results
    else:
        return "PASS", results


def main():
    """메인 실행"""
    parser = argparse.ArgumentParser(description='Part 9 자동 검증')
    parser.add_argument('--web', nargs='?', const='all', default=None,
                        help='웹 렌더링 검증 (section_id 또는 all)')
    args = parser.parse_args()

    print("=" * 60)
    if args.web:
        print("Part 9 자동 검증 (JSON + Web)")
    else:
        print("Part 9 자동 검증 (JSON only)")
    print("=" * 60)

    sections, tables = load_data()

    # 결과 저장
    pass_list = []
    warn_list = []
    fail_list = []
    skip_list = []

    # 섹션 목록 결정
    if args.web and args.web != 'all':
        # 특정 섹션만
        section_ids = [args.web]
    else:
        # 9.1 ~ 9.41 (9.34 제외)
        section_ids = [f"9.{i}" for i in range(1, 42) if i != 34]

    for section_id in section_ids:
        # JSON 검증
        status, messages = verify_section(section_id, sections, tables)

        # 웹 검증 (--web 옵션 시)
        web_status = None
        web_messages = []
        if args.web:
            web_ok, web_result = check_web_rendering(section_id)
            if isinstance(web_result, list):
                web_messages = web_result
            else:
                web_messages = [web_result]

            if not web_ok:
                web_status = "FAIL"
            elif any('[WARN]' in m for m in web_messages):
                web_status = "WARN"
            else:
                web_status = "PASS"

            # 웹 결과를 메시지에 추가
            messages = messages + [f"[WEB] {m}" for m in web_messages]

            # 웹 FAIL이면 전체 FAIL
            if web_status == "FAIL":
                status = "FAIL"
            elif web_status == "WARN" and status == "PASS":
                status = "WARN"

        # 결과 출력
        if status == "PASS":
            pass_list.append(section_id)
            print(f"[OK]   {section_id}: PASS")
        elif status == "WARN":
            warn_list.append((section_id, messages))
            print(f"[WARN] {section_id}: WARN")
            for msg in messages:
                print(f"       {msg}")
        elif status == "FAIL":
            fail_list.append((section_id, messages))
            print(f"[FAIL] {section_id}: FAIL")
            for msg in messages:
                print(f"       {msg}")
        else:
            skip_list.append(section_id)
            print(f"[SKIP] {section_id}: SKIP")

    # 요약
    print("\n" + "=" * 60)
    print("Result Summary")
    print("=" * 60)
    print(f"[OK]   PASS: {len(pass_list)}")
    print(f"[WARN] WARN: {len(warn_list)} (manual check recommended)")
    print(f"[FAIL] FAIL: {len(fail_list)} (/verify required)")
    print(f"[SKIP] SKIP: {len(skip_list)}")

    if fail_list:
        print("\n[FAIL] Sections:")
        for section_id, messages in fail_list:
            print(f"  - {section_id}")
            for msg in messages:
                print(f"      {msg}")

    if warn_list:
        print("\n[WARN] Sections:")
        for section_id, messages in warn_list:
            print(f"  - {section_id}")
            for msg in messages:
                print(f"      {msg}")

    print("\n" + "=" * 60)
    if args.web:
        print("Next Steps:")
        print("1. PASS -> No Playwright needed")
        print("2. WARN/FAIL -> Use Playwright for visual check")
    else:
        print("Next Steps:")
        print("1. Run with --web for web rendering check")
        print("2. FAIL sections -> run /verify [section_id]")
    print("=" * 60)


if __name__ == "__main__":
    main()
