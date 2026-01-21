"""
Ontario Building Code Part 9 파싱 스크립트
PDF에서 텍스트를 추출하고 JSON으로 구조화
"""

import fitz
import os
import sys
import re
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict

sys.stdout.reconfigure(encoding='utf-8')

# 경로 설정
BASE_PATH = "../../source/2024 Building Code Compendium"
PDF_FILE = "301880.pdf"
OUTPUT_DIR = "./output"

# Part 9 페이지 범위 (0-indexed)
PART9_START_PAGE = 714  # 실제 내용 시작 (Section 9.1)
PART9_END_PAGE = 986    # Part 9 끝

# 정규식 패턴
PATTERNS = {
    'section': re.compile(r'^Section\s+9\.(\d+)\.\s*(.+)$', re.MULTILINE),
    'subsection': re.compile(r'^9\.(\d+)\.(\d+)\.\s+(.+)$', re.MULTILINE),
    'article': re.compile(r'^9\.(\d+)\.(\d+)\.(\d+)[A-Z]?\.\s+(.+)$', re.MULTILINE),
    'sentence': re.compile(r'^\((\d+)\)\s+(.+)$', re.MULTILINE),
    'clause': re.compile(r'^\s*\(([a-z])\)\s+(.+)$', re.MULTILINE),
    'table': re.compile(r'^Table\s+9\.[\d.]+[A-Z]?\.\s*$', re.MULTILINE),
    'note': re.compile(r'\(See\s+Note\s+A-[\d.]+\)', re.IGNORECASE),
}


@dataclass
class Sentence:
    number: int
    text: str
    clauses: List[Dict[str, str]]


@dataclass
class Article:
    id: str
    title: str
    sentences: List[Sentence]
    tables: List[str]
    notes: List[str]


@dataclass
class Subsection:
    id: str
    title: str
    articles: List[Article]


@dataclass
class Section:
    id: str
    title: str
    subsections: List[Subsection]


def extract_text_from_pdf(pdf_path: str, start_page: int, end_page: int) -> str:
    """PDF에서 특정 페이지 범위의 텍스트 추출"""
    doc = fitz.open(pdf_path)
    text = ""

    for page_num in range(start_page, min(end_page, len(doc))):
        page = doc[page_num]
        page_text = page.get_text()
        text += page_text + "\n\n"

    doc.close()
    return text


def clean_text(text: str) -> str:
    """텍스트 정리"""
    # 페이지 헤더/푸터 제거
    text = re.sub(r'2024 Building Code Compendium\s*', '', text)
    text = re.sub(r'Division B – Part 9\s*\d*\s*', '', text)

    # 여러 공백을 하나로
    text = re.sub(r' +', ' ', text)

    # 줄바꿈 정리
    text = re.sub(r'\n\s*\n', '\n\n', text)

    return text.strip()


def parse_sentences(content: str) -> List[Dict]:
    """조항 (1), (2), ... 파싱"""
    sentences = []
    current_sentence = None
    current_clauses = []

    lines = content.split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # 새로운 sentence 시작
        sentence_match = PATTERNS['sentence'].match(line)
        if sentence_match:
            # 이전 sentence 저장
            if current_sentence is not None:
                sentences.append({
                    'number': current_sentence['number'],
                    'text': current_sentence['text'],
                    'clauses': current_clauses
                })
                current_clauses = []

            current_sentence = {
                'number': int(sentence_match.group(1)),
                'text': sentence_match.group(2)
            }
            continue

        # clause (a), (b), ... 파싱
        clause_match = PATTERNS['clause'].match(line)
        if clause_match and current_sentence:
            current_clauses.append({
                'letter': clause_match.group(1),
                'text': clause_match.group(2)
            })
            continue

        # 기존 sentence/clause에 텍스트 추가
        if current_clauses:
            current_clauses[-1]['text'] += ' ' + line
        elif current_sentence:
            current_sentence['text'] += ' ' + line

    # 마지막 sentence 저장
    if current_sentence is not None:
        sentences.append({
            'number': current_sentence['number'],
            'text': current_sentence['text'],
            'clauses': current_clauses
        })

    return sentences


def parse_part9(text: str) -> Dict:
    """Part 9 전체 파싱"""
    result = {
        'id': '9',
        'title': 'Housing and Small Buildings',
        'sections': []
    }

    # Section 단위로 분리
    section_splits = re.split(r'(Section\s+9\.\d+\.)', text)

    current_section = None

    for i, chunk in enumerate(section_splits):
        # Section 헤더 감지
        section_header_match = re.match(r'Section\s+9\.(\d+)\.', chunk)
        if section_header_match:
            section_num = section_header_match.group(1)

            # 다음 chunk가 제목과 내용
            if i + 1 < len(section_splits):
                content = section_splits[i + 1]

                # 첫 줄에서 제목 추출
                lines = content.strip().split('\n')
                title = lines[0].strip() if lines else f"Section 9.{section_num}"

                current_section = {
                    'id': f'9.{section_num}',
                    'title': title,
                    'subsections': []
                }

                # Subsection 파싱
                subsections = parse_subsections(content, section_num)
                current_section['subsections'] = subsections

                result['sections'].append(current_section)

    return result


def parse_subsections(content: str, section_num: str) -> List[Dict]:
    """Subsection (9.x.y) 파싱"""
    subsections = []

    # 9.x.y. 패턴으로 분리
    pattern = rf'(9\.{section_num}\.(\d+)\.)\s+'
    splits = re.split(pattern, content)

    i = 0
    while i < len(splits):
        chunk = splits[i]

        # Subsection 헤더 감지
        subsec_match = re.match(rf'9\.{section_num}\.(\d+)\.', chunk)
        if subsec_match:
            subsec_num = subsec_match.group(1)

            # 다음 chunk가 제목과 내용
            if i + 2 < len(splits):
                next_chunk = splits[i + 2]

                # 첫 줄에서 제목 추출
                lines = next_chunk.strip().split('\n')
                title = lines[0].strip() if lines else ""

                # (1)로 시작하는 부분부터가 실제 내용
                content_start = next_chunk.find('(1)')
                article_content = next_chunk[content_start:] if content_start > 0 else next_chunk

                subsection = {
                    'id': f'9.{section_num}.{subsec_num}',
                    'title': title,
                    'articles': []
                }

                # Article 파싱 (단순화: sentences만 추출)
                sentences = parse_sentences(article_content)
                if sentences:
                    subsection['articles'].append({
                        'id': f'9.{section_num}.{subsec_num}.1',
                        'title': title,
                        'sentences': sentences,
                        'tables': [],
                        'notes': []
                    })

                subsections.append(subsection)

        i += 1

    return subsections


def save_json(data: Dict, filename: str):
    """JSON 파일로 저장"""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    filepath = os.path.join(OUTPUT_DIR, filename)

    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    print(f"저장됨: {filepath}")


def main():
    script_dir = os.path.dirname(os.path.abspath(__file__))
    pdf_path = os.path.normpath(os.path.join(script_dir, BASE_PATH, PDF_FILE))

    print(f"PDF 경로: {pdf_path}")
    print(f"파싱 범위: Page {PART9_START_PAGE + 1} ~ {PART9_END_PAGE}")

    # 1. PDF에서 텍스트 추출
    print("\n1. PDF에서 텍스트 추출 중...")
    raw_text = extract_text_from_pdf(pdf_path, PART9_START_PAGE, PART9_END_PAGE)
    print(f"   추출된 텍스트 길이: {len(raw_text):,} 문자")

    # 2. 텍스트 정리
    print("\n2. 텍스트 정리 중...")
    cleaned_text = clean_text(raw_text)
    print(f"   정리된 텍스트 길이: {len(cleaned_text):,} 문자")

    # 3. 구조화된 데이터로 파싱
    print("\n3. 구조화된 데이터로 파싱 중...")
    part9_data = parse_part9(cleaned_text)
    print(f"   섹션 수: {len(part9_data['sections'])}")

    # 4. JSON 저장
    print("\n4. JSON 저장 중...")
    save_json(part9_data, 'part9.json')

    # 5. 요약 출력
    print("\n=== 파싱 결과 요약 ===")
    for section in part9_data['sections'][:10]:  # 처음 10개만
        print(f"  {section['id']}: {section['title']}")
        for subsec in section['subsections'][:3]:  # 처음 3개만
            print(f"    └─ {subsec['id']}: {subsec['title']}")

    print("\n완료!")


if __name__ == "__main__":
    main()
