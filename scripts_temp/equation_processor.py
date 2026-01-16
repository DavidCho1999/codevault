"""
Building Code 수식 감지 및 LaTeX 변환 스크립트
- PDF 파싱 후 텍스트에서 수식 패턴 감지
- LaTeX 마커($...$) 추가
- JSON 저장 시 수식 포함
"""

import re
import json
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

# Building Code에서 자주 사용되는 수식 패턴들
EQUATION_PATTERNS = [
    # R-value 공식
    (r'R\s*=\s*1\s*/\s*U', r'$R = \\frac{1}{U}$'),
    (r'RSI\s*=\s*1\s*/\s*U', r'$RSI = \\frac{1}{U}$'),
    (r'U\s*=\s*1\s*/\s*R', r'$U = \\frac{1}{R}$'),

    # 열관류율 공식
    (r'(\w+)\s*=\s*(\d+(?:\.\d+)?)\s*/\s*(\d+(?:\.\d+)?)', r'$\1 = \\frac{\2}{\3}$'),

    # 면적 단위: m², m³, ft², etc.
    (r'(\d+(?:\.\d+)?)\s*m²', r'$\1\\text{ m}^2$'),
    (r'(\d+(?:\.\d+)?)\s*m³', r'$\1\\text{ m}^3$'),
    (r'(\d+(?:\.\d+)?)\s*ft²', r'$\1\\text{ ft}^2$'),
    (r'(\d+(?:\.\d+)?)\s*ft³', r'$\1\\text{ ft}^3$'),
    (r'(\d+(?:\.\d+)?)\s*mm²', r'$\1\\text{ mm}^2$'),

    # 단위 없는 제곱/세제곱
    (r'\bm²\b', r'$\\text{m}^2$'),
    (r'\bm³\b', r'$\\text{m}^3$'),
    (r'\bft²\b', r'$\\text{ft}^2$'),
    (r'\bft³\b', r'$\\text{ft}^3$'),
    (r'\bmm²\b', r'$\\text{mm}^2$'),

    # 온도 기호
    (r'(\d+(?:\.\d+)?)\s*°\s*C', r'$\1°\\text{C}$'),
    (r'(\d+(?:\.\d+)?)\s*°\s*F', r'$\1°\\text{F}$'),

    # 부등호
    (r'>=', r'$\\geq$'),
    (r'<=', r'$\\leq$'),
    (r'≥', r'$\\geq$'),
    (r'≤', r'$\\leq$'),

    # 플러스마이너스
    (r'\+/-', r'$\\pm$'),
    (r'±', r'$\\pm$'),

    # 과학적 표기법
    (r'(\d+(?:\.\d+)?)\s*[×x]\s*10\^(\d+)', r'$\1 \\times 10^{\2}$'),
    (r'(\d+(?:\.\d+)?)\s*[×x]\s*10(\d+)', r'$\1 \\times 10^{\2}$'),

    # 하중 계산식 (Building Code 특유)
    (r'([A-Za-z]+)\s*=\s*([A-Za-z0-9]+)\s*\+\s*([A-Za-z0-9]+)', r'$\1 = \2 + \3$'),

    # 비율 (slope, ratio)
    (r'(\d+)\s*:\s*(\d+)', r'$\1:\2$'),

    # 제곱근
    (r'sqrt\s*\(\s*([^)]+)\s*\)', r'$\\sqrt{\1}$'),
    (r'√\s*(\d+(?:\.\d+)?)', r'$\\sqrt{\1}$'),
]

# 수식이 포함되었는지 감지하는 패턴
EQUATION_INDICATORS = [
    r'[=<>≤≥±]',          # 수학 기호
    r'\d+\s*/\s*\d+',     # 분수 형태
    r'[²³√∑∫∏]',           # 수학 특수문자
    r'\d+\s*[×x]\s*10',   # 과학적 표기법
    r'\bsqrt\s*\(',       # 제곱근
    r'm²|m³|ft²|ft³',     # 면적/부피 단위
    r'°\s*[CF]',          # 온도
]


def has_equation(text: str) -> bool:
    """텍스트에 수식이 포함되어 있는지 감지"""
    for pattern in EQUATION_INDICATORS:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def convert_equations(text: str) -> str:
    """텍스트 내 수식 패턴을 LaTeX 마커로 변환"""
    result = text

    for pattern, replacement in EQUATION_PATTERNS:
        try:
            result = re.sub(pattern, replacement, result)
        except Exception as e:
            print(f"  Warning: Pattern error '{pattern}': {e}")

    return result


def process_content(content: str) -> tuple[str, int]:
    """
    콘텐츠 전체를 처리하여 수식을 LaTeX로 변환
    Returns: (processed_content, equation_count)
    """
    if not content:
        return content, 0

    lines = content.split('\n')
    processed_lines = []
    equation_count = 0

    for line in lines:
        if has_equation(line):
            converted = convert_equations(line)
            if converted != line:
                equation_count += 1
            processed_lines.append(converted)
        else:
            processed_lines.append(line)

    return '\n'.join(processed_lines), equation_count


def process_json_file(input_path: str, output_path: str) -> dict:
    """JSON 파일을 읽어 수식 처리 후 저장"""
    with open(input_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    stats = {
        'total_sections': 0,
        'sections_with_equations': 0,
        'total_equations': 0
    }

    if isinstance(data, list):
        # 섹션 리스트 형태
        for section in data:
            stats['total_sections'] += 1
            if 'content' in section and section['content']:
                processed, count = process_content(section['content'])
                section['content'] = processed
                if count > 0:
                    stats['sections_with_equations'] += 1
                    stats['total_equations'] += count
    elif isinstance(data, dict):
        # 딕셔너리 형태
        for key, section in data.items():
            stats['total_sections'] += 1
            if isinstance(section, dict) and 'content' in section and section['content']:
                processed, count = process_content(section['content'])
                section['content'] = processed
                if count > 0:
                    stats['sections_with_equations'] += 1
                    stats['total_equations'] += count

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return stats


def test_patterns():
    """패턴 테스트"""
    test_cases = [
        "R = 1/U for thermal resistance",
        "minimum area of 15 m² required",
        "slope ratio of 1:12",
        "temperature not less than 20°C",
        "load factor >= 1.5",
        "tolerance of ±5 mm",
        "pressure of 2.5 × 10^6 Pa",
        "calculate sqrt(144) = 12",
        "Dead load D = 1.5 + 0.5",
    ]

    print("=" * 60)
    print("수식 패턴 테스트")
    print("=" * 60)

    for test in test_cases:
        if has_equation(test):
            converted = convert_equations(test)
            print(f"\nOriginal: {test}")
            print(f"Converted: {converted}")
        else:
            print(f"\nNo equation: {test}")


def main():
    import argparse

    parser = argparse.ArgumentParser(description='Building Code 수식 변환기')
    parser.add_argument('--input', '-i', help='입력 JSON 파일')
    parser.add_argument('--output', '-o', help='출력 JSON 파일')
    parser.add_argument('--test', '-t', action='store_true', help='패턴 테스트')

    args = parser.parse_args()

    if args.test:
        test_patterns()
        return

    if args.input:
        input_path = args.input
        output_path = args.output or input_path.replace('.json', '_equations.json')

        print(f"Processing: {input_path}")
        stats = process_json_file(input_path, output_path)

        print(f"\n완료!")
        print(f"  처리 섹션: {stats['total_sections']}")
        print(f"  수식 포함 섹션: {stats['sections_with_equations']}")
        print(f"  총 변환 수식: {stats['total_equations']}")
        print(f"  저장: {output_path}")
    else:
        # 기본: 테스트 실행
        test_patterns()


if __name__ == '__main__':
    main()
