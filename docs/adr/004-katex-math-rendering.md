# ADR-004: KaTeX 수식 렌더링

## 상태
Accepted

## 맥락

Ontario Building Code에는 열전달, 구조 계산 등의 수학 공식이 포함되어 있습니다.
PDF에서 추출한 텍스트 형태의 수식을 웹에서 보기 좋게 렌더링해야 했습니다.

### 요구사항
- 수학 공식을 전문적으로 표시
- 빠른 렌더링 성능
- 작은 번들 크기
- 접근성 지원 (스크린 리더)

### 수식 예시
```
R = 1/U               → 분수
5°C                   → 온도 단위
m²                    → 제곱
alpha, beta           → 그리스 문자
A_1, A₂               → 아래첨자
```

## 결정

**KaTeX를 사용하여 텍스트 패턴을 LaTeX로 변환 후 렌더링한다.**

```typescript
// src/components/code/EquationRenderer.tsx

// 텍스트 → LaTeX 변환
export function textToLatex(text: string): string {
  let latex = text;

  // 분수: R = 1/U → R = \frac{1}{U}
  latex = latex.replace(/(\w+)\s*=\s*(\d+)\/(\w+)/g,
    '$1 = \\frac{$2}{$3}');

  // 온도: 5°C → 5°\text{C}
  latex = latex.replace(/(\d+)°([CF])/g, '$1°\\text{$2}');

  // 제곱: m² → \text{m}^2
  latex = latex.replace(/(\w+)²/g, '\\text{$1}^2');

  // 그리스 문자
  const greekLetters = {
    'alpha': '\\alpha', 'beta': '\\beta',
    'gamma': '\\gamma', 'delta': '\\delta'
  };
  for (const [name, symbol] of Object.entries(greekLetters)) {
    latex = latex.replace(new RegExp(name, 'gi'), symbol);
  }

  return latex;
}

// KaTeX 렌더링
import katex from 'katex';

export function renderKatex(latex: string): string {
  return katex.renderToString(latex, {
    throwOnError: false,
    trust: true
  });
}
```

## 선택지

### 선택지 1: KaTeX ✓ 선택됨
- **장점**:
  - 매우 빠른 렌더링 (MathJax의 10배)
  - 작은 번들 크기 (~200KB)
  - 서버 사이드 렌더링 지원
  - 동기 API (간단)
  - 접근성 지원 (aria 속성)
- **단점**:
  - MathJax보다 LaTeX 기능 제한
  - 일부 복잡한 수식 미지원

### 선택지 2: MathJax
- **장점**:
  - 완전한 LaTeX 지원
  - 다양한 출력 포맷 (HTML, SVG, MathML)
  - 널리 사용됨
- **단점**:
  - 느린 렌더링
  - 큰 번들 크기 (~1MB)
  - 비동기 API (복잡)

### 선택지 3: Plain Text/Unicode
- **장점**:
  - 의존성 없음
  - 번들 크기 영향 없음
  - 복사/붙여넣기 용이
- **단점**:
  - 전문적이지 않은 표시
  - 복잡한 수식 표현 불가
  - 분수, 루트 등 표현 어려움

### 선택지 4: 이미지 (SVG/PNG)
- **장점**:
  - 정확한 표시
  - 렌더링 일관성
- **단점**:
  - 접근성 문제 (스크린 리더)
  - 확대 시 품질 저하 (PNG)
  - 수정 어려움

## 결과

### 긍정적
- 빠른 수식 렌더링 (< 1ms per equation)
- 전문적인 수학 표기
- 접근성 지원 (`aria-label`)
- 복사 시 LaTeX 코드 유지
- react-katex로 React 통합 용이

### 부정적
- 번들 크기 증가 (~200KB)
- 텍스트 → LaTeX 변환 로직 유지 필요
- 일부 PDF 수식이 텍스트로 추출되지 않을 수 있음

### 변환 패턴 목록

| Input Pattern | LaTeX Output | 설명 |
|---------------|--------------|------|
| `R = 1/U` | `R = \frac{1}{U}` | 분수 |
| `5°C` | `5°\text{C}` | 온도 |
| `m²`, `m³` | `\text{m}^2`, `\text{m}^3` | 제곱/세제곱 |
| `alpha` | `\alpha` | 그리스 문자 |
| `A_1` | `A_1` | 아래첨자 |
| `≥`, `≤` | `\geq`, `\leq` | 부등호 |

## 참고
- [KaTeX Documentation](https://katex.org/)
- [react-katex](https://github.com/talyssonoc/react-katex)
- [KaTeX vs MathJax](https://www.intmath.com/cg5/katex-mathjax-comparison.php)
