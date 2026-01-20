"use client";

import { useMemo } from "react";
import DOMPurify from "dompurify";
import katex from "katex";
import "katex/dist/katex.min.css";

interface EquationRendererProps {
  text: string;
  displayMode?: boolean;
}

// Building Code에서 자주 사용되는 수식 패턴들
const EQUATION_PATTERNS: [RegExp, (match: RegExpMatchArray) => string][] = [
  // R-value: R = 1/U or RSI = 1/U
  [/R\s*=\s*1\s*\/\s*U/gi, () => "R = \\frac{1}{U}"],
  [/RSI\s*=\s*1\s*\/\s*U/gi, () => "RSI = \\frac{1}{U}"],

  // Fractions: a/b 형태 (단순 숫자)
  [/(\d+(?:\.\d+)?)\s*\/\s*(\d+(?:\.\d+)?)/g, (m) => `\\frac{${m[1]}}{${m[2]}}`],

  // Square root: sqrt(x) or √x
  [/sqrt\s*\(\s*([^)]+)\s*\)/gi, (m) => `\\sqrt{${m[1]}}`],
  [/√\s*(\d+(?:\.\d+)?)/g, (m) => `\\sqrt{${m[1]}}`],

  // Superscript for units: m², m³, ft², etc.
  [/(\d+(?:\.\d+)?)\s*(m|ft|mm|cm|in)²/gi, (m) => `${m[1]}\\text{ ${m[2]}}^2`],
  [/(\d+(?:\.\d+)?)\s*(m|ft|mm|cm|in)³/gi, (m) => `${m[1]}\\text{ ${m[2]}}^3`],
  [/(m|ft|mm|cm|in)²/gi, (m) => `\\text{${m[1]}}^2`],
  [/(m|ft|mm|cm|in)³/gi, (m) => `\\text{${m[1]}}^3`],

  // Temperature: °C, °F
  [/(\d+(?:\.\d+)?)\s*°\s*C/gi, (m) => `${m[1]}°\\text{C}`],
  [/(\d+(?:\.\d+)?)\s*°\s*F/gi, (m) => `${m[1]}°\\text{F}`],

  // Scientific notation: 1.5 x 10^6
  [/(\d+(?:\.\d+)?)\s*[×x]\s*10\^(\d+)/gi, (m) => `${m[1]} \\times 10^{${m[2]}}`],

  // Greater than or equal, less than or equal
  [/>=|≥/g, () => "\\geq"],
  [/<=|≤/g, () => "\\leq"],

  // Plus-minus symbol
  [/\+\/-|±/g, () => "\\pm"],

  // Greek letters commonly used
  [/\balpha\b/gi, () => "\\alpha"],
  [/\bbeta\b/gi, () => "\\beta"],
  [/\bgamma\b/gi, () => "\\gamma"],
  [/\bdelta\b/gi, () => "\\delta"],
  [/\bphi\b/gi, () => "\\phi"],
  [/\blambda\b/gi, () => "\\lambda"],
  [/\bmu\b/gi, () => "\\mu"],
  [/\brho\b/gi, () => "\\rho"],
  [/\bsigma\b/gi, () => "\\sigma"],
  [/\btheta\b/gi, () => "\\theta"],

  // Subscripts: X_sub, X₁, X₂, etc.
  [/([A-Za-z])_([a-zA-Z0-9]+)/g, (m) => `${m[1]}_{${m[2]}}`],
  [/([A-Za-z])₁/g, (m) => `${m[1]}_1`],
  [/([A-Za-z])₂/g, (m) => `${m[1]}_2`],
  [/([A-Za-z])₃/g, (m) => `${m[1]}_3`],

  // Summation: sum of or Σ
  [/Σ\s*([A-Za-z0-9]+)/g, (m) => `\\sum ${m[1]}`],
];

// 수식이 포함된 텍스트인지 감지 (보수적 접근)
function hasEquation(text: string): boolean {
  // 명시적 LaTeX 마커가 있으면 true
  if (/\$[^$]+\$/.test(text)) return true;

  // 특수 수학 문자가 있으면 true
  if (/[²³√∑∫∏≤≥±]/.test(text)) return true;

  // 온도 표기 (예: 5°C)
  if (/\d+\s*°\s*[CF]\b/.test(text)) return true;

  // 과학적 표기법 (예: 2.5 × 10^6)
  if (/\d+\s*[×x]\s*10\^\d+/i.test(text)) return true;

  // 순수 수학 공식 (예: R = 1/U) - 짧은 수식만
  if (/^[A-Z]\s*=\s*\d+\s*\/\s*[A-Z]$/i.test(text.trim())) return true;
  if (/^[A-Z]\s*=\s*1\s*\/\s*[A-Z]$/i.test(text.trim())) return true;

  return false;
}

// 텍스트를 LaTeX로 변환
function textToLatex(text: string): string {
  let latex = text;

  for (const [pattern, replacer] of EQUATION_PATTERNS) {
    latex = latex.replace(pattern, (match, ...groups) => {
      const matchArray = [match, ...groups] as RegExpMatchArray;
      return replacer(matchArray);
    });
  }

  return latex;
}

// KaTeX로 렌더링
function renderKatex(latex: string, displayMode: boolean): string {
  try {
    return katex.renderToString(latex, {
      displayMode,
      throwOnError: false,
      errorColor: "#cc0000",
      strict: false,
      trust: true,
    });
  } catch (error) {
    console.error("KaTeX rendering error:", error);
    return latex; // 실패시 원본 반환
  }
}

// 인라인 수식 패턴들 (텍스트 내에서 부분적으로 변환)
const INLINE_PATTERNS: [RegExp, string][] = [
  // 온도: 5°C, 10°F
  [/(\d+(?:\.\d+)?)\s*°\s*C\b/g, '$1°C'],
  [/(\d+(?:\.\d+)?)\s*°\s*F\b/g, '$1°F'],

  // 면적/부피 단위: 15 m², 20 m³
  [/(\d+(?:\.\d+)?)\s*m²/g, '$1 m²'],
  [/(\d+(?:\.\d+)?)\s*m³/g, '$1 m³'],
  [/(\d+(?:\.\d+)?)\s*ft²/g, '$1 ft²'],
  [/(\d+(?:\.\d+)?)\s*mm²/g, '$1 mm²'],

  // 부등호
  [/\s*>=\s*/g, ' ≥ '],
  [/\s*<=\s*/g, ' ≤ '],

  // 플러스마이너스
  [/\+\/-/g, '±'],
];

// 텍스트에서 수식 부분만 분리하여 렌더링
function parseAndRenderEquations(text: string): { html: string; hasEquations: boolean } {
  // 명시적 수식 마커 체크: $...$ 또는 $$...$$
  const inlineRegex = /\$([^$]+)\$/g;
  const displayRegex = /\$\$([^$]+)\$\$/g;

  let result = text;
  let hasEquations = false;

  // Display mode 수식 처리 ($$...$$)
  result = result.replace(displayRegex, (_, latex) => {
    hasEquations = true;
    return `<div class="my-2">${renderKatex(latex, true)}</div>`;
  });

  // Inline 수식 처리 ($...$)
  result = result.replace(inlineRegex, (_, latex) => {
    hasEquations = true;
    return renderKatex(latex, false);
  });

  // 명시적 마커가 없으면 인라인 패턴만 적용 (유니코드 문자로 변환)
  if (!hasEquations) {
    for (const [pattern, replacement] of INLINE_PATTERNS) {
      if (pattern.test(result)) {
        result = result.replace(pattern, replacement);
        hasEquations = true;
      }
    }
  }

  // <sup> 태그 처리: <sup>2</sup> → ² 등으로 변환
  if (/<sup>/i.test(result)) {
    result = result
      .replace(/<sup>2<\/sup>/gi, '²')
      .replace(/<sup>3<\/sup>/gi, '³')
      .replace(/<sup>o<\/sup>/gi, '°')
      .replace(/<sup>1<\/sup>/gi, '¹')
      .replace(/<sup>([^<]+)<\/sup>/gi, '<sup>$1</sup>'); // 나머지는 그대로 유지
    hasEquations = true;
  }

  return { html: result, hasEquations };
}

export default function EquationRenderer({ text, displayMode = false }: EquationRendererProps) {
  const rendered = useMemo(() => {
    if (!text) return { html: "", hasEquations: false, hasKatex: false };

    const result = parseAndRenderEquations(text);
    // KaTeX HTML이 포함되어 있는지 확인
    const hasKatex = result.html.includes('class="katex"');

    return { ...result, hasKatex };
  }, [text]);

  // KaTeX 렌더링이 필요한 경우만 dangerouslySetInnerHTML 사용
  if (rendered.hasKatex) {
    return (
      <span
        className="equation-rendered"
        dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(rendered.html) }}
      />
    );
  }

  // 유니코드 변환만 있는 경우 또는 변환 없는 경우
  return <>{rendered.hasEquations ? rendered.html : text}</>;
}

// 텍스트 전체를 수식으로 렌더링 (직접 LaTeX 입력)
export function MathBlock({ latex, display = true }: { latex: string; display?: boolean }) {
  const html = useMemo(() => DOMPurify.sanitize(renderKatex(latex, display)), [latex, display]);

  return (
    <div
      className={display ? "my-4 text-center" : "inline"}
      dangerouslySetInnerHTML={{ __html: html }}
    />
  );
}

// 유틸리티 함수 export
export { hasEquation, textToLatex, renderKatex };
