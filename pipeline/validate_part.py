#!/usr/bin/env python3
"""
Part JSON 검증 스크립트
새로운 Part를 파싱한 후 품질 검증을 위해 사용

사용법:
    python scripts/validate_part.py codevault/public/data/part10.json
    python scripts/validate_part.py obc.db --db --part 10
"""

import json
import re
import sys
import sqlite3
import io

# Windows 콘솔 인코딩 설정
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
from pathlib import Path
from typing import List, Dict, Tuple
from collections import defaultdict


class ParsingValidator:
    def __init__(self):
        self.errors: List[Tuple[str, str, str]] = []  # (level, node_id, message)
        self.warnings: List[Tuple[str, str, str]] = []
        self.stats = defaultdict(int)

    def validate_json(self, json_path: str) -> bool:
        """JSON 파일 검증"""
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        print(f"\n{'='*60}")
        print(f"Validating: {json_path}")
        print(f"{'='*60}")

        if isinstance(data, list):
            for node in data:
                self._validate_node_recursive(node)
        elif isinstance(data, dict):
            self._validate_node_recursive(data)

        return self._report()

    def validate_db(self, db_path: str, part: str) -> bool:
        """SQLite DB에서 특정 Part 검증"""
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        print(f"\n{'='*60}")
        print(f"Validating Part {part} from: {db_path}")
        print(f"{'='*60}")

        # Part 번호로 시작하는 모든 노드 가져오기
        cursor.execute(
            "SELECT id, title, content FROM nodes WHERE id LIKE ?",
            (f"{part}.%",)
        )

        for row in cursor.fetchall():
            node_id, title, content = row
            self._validate_node({
                'id': node_id,
                'title': title or '',
                'content': content or ''
            })

        conn.close()
        return self._report()

    def _validate_node_recursive(self, node: Dict):
        """노드와 하위 노드들을 재귀적으로 검증"""
        self._validate_node(node)

        # 하위 노드들 재귀 탐색
        for key in ['sections', 'subsections', 'articles']:
            if key in node and isinstance(node[key], list):
                for child in node[key]:
                    self._validate_node_recursive(child)

    def _validate_node(self, node: Dict):
        """단일 노드 검증"""
        node_id = node.get('id', 'unknown')
        content = node.get('content', '')
        title = node.get('title', '')

        self.stats['total_nodes'] += 1

        if not content:
            self.warnings.append(('WARN', node_id, 'Empty content'))
            return

        self.stats['total_content_length'] += len(content)

        # 1. 마크다운 헤딩 잔류 검사
        if re.search(r'^#{2,4}\s+', content, re.MULTILINE):
            self.errors.append(('ERROR', node_id, 'RAW_MARKDOWN_HEADING: ###/##/#### 마크다운 헤딩 잔류'))

        # 2. 볼드 마크다운 잔류 검사
        if re.search(r'^\*\*[A-Z].*\*\*$', content, re.MULTILINE):
            self.errors.append(('ERROR', node_id, 'RAW_BOLD: **볼드** 마크다운 잔류'))

        # 3. 이탤릭 마크다운 잔류 검사 (볼드 제외)
        if re.search(r'^\*[A-Z].*[^*]\*$', content, re.MULTILINE):
            if not re.search(r'^\*\*', content, re.MULTILINE):
                self.warnings.append(('WARN', node_id, 'RAW_ITALIC: *이탤릭* 마크다운 잔류 가능성'))

        # 4. Flat table 패턴 검사 (C.A. Number)
        if re.search(r'C\.A\.\s*Number.*Division B.*Compliance', content, re.IGNORECASE):
            if not re.search(r'<table[\s>]', content, re.IGNORECASE):
                self.errors.append(('ERROR', node_id, 'FLAT_TABLE: C.A. Number 테이블이 <table>로 변환 안됨'))

        # 5. H.I. 테이블 패턴 검사
        if re.search(r'(?:Small|Medium|Large)\s+(?:Small|Medium|Large)\s+\d', content):
            if not re.search(r'<table[\s>]', content, re.IGNORECASE):
                self.warnings.append(('WARN', node_id, 'POSSIBLE_FLAT_HI_TABLE: H.I. 테이블 flat text 가능성'))

        # 6. 테이블 헤딩 vs <table> 태그 불일치 검사
        table_headings = re.findall(r'Table\s+\d+\.\d+\.\d+\.?\d*-[A-Z]', content)
        table_tags = re.findall(r'<table', content, re.IGNORECASE)
        if len(table_headings) > len(table_tags) + 2:
            self.warnings.append(('WARN', node_id,
                f'TABLE_MISMATCH: 테이블 헤딩 {len(table_headings)}개, <table> {len(table_tags)}개'))

        # 7. 짧은 content 검사 (Subsection인데 너무 짧으면)
        parts = node_id.split('.')
        if len(parts) == 3 and len(content) < 100:  # Subsection level
            self.warnings.append(('WARN', node_id, f'SHORT_CONTENT: Subsection인데 {len(content)}자만 있음'))

        # 8. 깨진 HTML 태그 검사
        open_tables = len(re.findall(r'<table', content, re.IGNORECASE))
        close_tables = len(re.findall(r'</table>', content, re.IGNORECASE))
        if open_tables != close_tables:
            self.errors.append(('ERROR', node_id,
                f'BROKEN_HTML: <table> {open_tables}개, </table> {close_tables}개'))

        # 9. PDF 페이지 분리 징후 검사
        if re.search(r'\d{4}\s+Building Code', content):
            self.warnings.append(('WARN', node_id, 'PDF_HEADER_LEAK: PDF 헤더가 content에 포함됨'))

        # 10. Raw HTML 태그 잔류 검사 (<sup>, <sub> 등)
        raw_html_match = re.search(r'<(sup|sub|em|strong|b|i)>[^<]*</(sup|sub|em|strong|b|i)>', content, re.IGNORECASE)
        if raw_html_match:
            self.warnings.append(('WARN', node_id, f'RAW_HTML_TAG: <{raw_html_match.group(1)}> 태그 잔류 - 유니코드로 변환 필요'))

        # 11. Clause 연속 텍스트 분리 검사
        # (a), (b), (c) 뒤에 바로 소문자로 시작하는 별도 줄이 있으면 경고
        # 예: "(c) something,\nwill result in..." → 연속 텍스트가 잘못 분리됨
        separated_continuation = re.search(r'\([a-z]\)[^\n]*[,;]\s*\n[a-z]', content)
        if separated_continuation:
            snippet = separated_continuation.group()[:50].replace('\n', '\\n')
            self.warnings.append(('WARN', node_id, f'SEPARATED_CONTINUATION: clause 뒤 연속 텍스트 분리 의심 - "{snippet}..."'))

        # 12. (See Note...) 패턴 독립 줄 검사
        # (See Note...)가 새 줄에서 시작하면 앞 clause와 분리된 것일 수 있음
        see_note_newline = re.search(r'\n\s*\(See\s+Note\s+[A-Z]?-?\d', content, re.IGNORECASE)
        if see_note_newline:
            self.warnings.append(('WARN', node_id, 'SEPARATED_SEE_NOTE: (See Note...) 패턴이 별도 줄 - 앞 clause와 분리 의심'))

        # 13. 인라인 마크다운 잔류 검사
        # 예: (**4)** 볼드 clause 번호, *header line* 이탤릭 용어
        inline_bold = re.search(r'\(\*\*\d+\)\*\*', content)  # (**4)**
        if inline_bold:
            self.errors.append(('ERROR', node_id, f'INLINE_BOLD: 인라인 볼드 마크다운 잔류 - "{inline_bold.group()}"'))

        inline_italic = re.search(r'(?<!\*)\*[a-zA-Z][^*\n]{1,30}\*(?!\*)', content)  # *italic term*
        if inline_italic:
            self.warnings.append(('WARN', node_id, f'INLINE_ITALIC: 인라인 이탤릭 마크다운 잔류 - "{inline_italic.group()}"'))

        # 통계
        if '<table' in content.lower():
            self.stats['nodes_with_tables'] += 1
        self.stats['table_tags'] += len(table_tags)
        self.stats['table_headings'] += len(table_headings)

    def _report(self) -> bool:
        """검증 결과 출력"""
        print(f"\n📊 Statistics:")
        print(f"   Total nodes: {self.stats['total_nodes']}")
        print(f"   Total content length: {self.stats['total_content_length']:,} chars")
        print(f"   Nodes with tables: {self.stats['nodes_with_tables']}")
        print(f"   Table headings found: {self.stats['table_headings']}")
        print(f"   <table> tags found: {self.stats['table_tags']}")

        if self.errors:
            print(f"\n❌ Errors ({len(self.errors)}):")
            for level, node_id, msg in self.errors:
                print(f"   [{node_id}] {msg}")

        if self.warnings:
            print(f"\n⚠️  Warnings ({len(self.warnings)}):")
            for level, node_id, msg in self.warnings[:20]:  # 최대 20개만 출력
                print(f"   [{node_id}] {msg}")
            if len(self.warnings) > 20:
                print(f"   ... and {len(self.warnings) - 20} more warnings")

        if not self.errors and not self.warnings:
            print(f"\n✅ All checks passed!")
            return True
        elif not self.errors:
            print(f"\n✅ No errors, but {len(self.warnings)} warnings")
            return True
        else:
            print(f"\n❌ {len(self.errors)} errors, {len(self.warnings)} warnings")
            return False


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python validate_part.py <json_file>")
        print("  python validate_part.py <db_file> --db --part <part_number>")
        print("\nExamples:")
        print("  python validate_part.py codevault/public/data/part10.json")
        print("  python validate_part.py obc.db --db --part 11")
        sys.exit(1)

    validator = ParsingValidator()

    if '--db' in sys.argv:
        db_path = sys.argv[1]
        part_idx = sys.argv.index('--part') + 1
        part = sys.argv[part_idx]
        success = validator.validate_db(db_path, part)
    else:
        json_path = sys.argv[1]
        success = validator.validate_json(json_path)

    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()
