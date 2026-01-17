"use client";

import { useMemo, Fragment } from "react";
import EquationRenderer from "./EquationRenderer";
import { parseReferences } from "./CrossReferenceLink";
import { parseDefinitions } from "./DefinitionTooltip";
import { useHighlight } from "./HighlightContext";

interface TextRendererProps {
  text: string;
}

/**
 * Note 참조를 스타일링 (See Note A-X.X.X.X.)
 */
function parseNotes(text: string): (string | React.ReactNode)[] {
  if (!text) return [text];

  const result: (string | React.ReactNode)[] = [];
  // (See Note A-X.X.X.X.) 또는 (See Notes A-X.X.X.X. and A-X.X.X.X.)
  const notePattern = /(\(See\s+Notes?\s+A-[\d.]+(?:\s+and\s+A-[\d.]+)*\.?\))/gi;

  let lastIndex = 0;
  let match;
  let keyIndex = 0;

  while ((match = notePattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      result.push(text.slice(lastIndex, match.index));
    }

    result.push(
      <span
        key={`note-${keyIndex++}`}
        className="text-amber-600 text-sm italic"
        title="참조 노트"
      >
        {match[1]}
      </span>
    );

    lastIndex = notePattern.lastIndex;
  }

  if (lastIndex < text.length) {
    result.push(text.slice(lastIndex));
  }

  return result.length > 0 ? result : [text];
}

/**
 * 검색어를 하이라이트 처리
 */
function parseHighlight(text: string, highlight: string | null): (string | React.ReactNode)[] {
  if (!highlight || !text) return [text];

  const result: (string | React.ReactNode)[] = [];
  // 대소문자 무시하고 검색어 매칭
  const pattern = new RegExp(`(${highlight.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")})`, "gi");

  let lastIndex = 0;
  let match;
  let keyIndex = 0;

  while ((match = pattern.exec(text)) !== null) {
    // 매칭 이전 텍스트
    if (match.index > lastIndex) {
      result.push(text.slice(lastIndex, match.index));
    }

    // 매칭된 텍스트를 mark로 감싸기
    result.push(
      <mark
        key={`highlight-${keyIndex++}`}
        className="bg-yellow-200 text-yellow-900 px-0.5 rounded"
      >
        {match[1]}
      </mark>
    );

    lastIndex = pattern.lastIndex;
  }

  // 남은 텍스트
  if (lastIndex < text.length) {
    result.push(text.slice(lastIndex));
  }

  return result.length > 0 ? result : [text];
}

/**
 * 텍스트를 렌더링하며 다음을 처리:
 * 1. Cross-Reference 링크 (Article, Table 등)
 * 2. Definition 용어 툴팁
 * 3. 검색어 하이라이트
 * 4. 수식 렌더링 (온도, 단위 등)
 */
export default function TextRenderer({ text }: TextRendererProps) {
  const { highlight } = useHighlight();

  const rendered = useMemo(() => {
    if (!text) return null;

    // 1단계: 참조 파싱 (Article, Table 등)
    const refParts = parseReferences(text);

    // 2단계: 각 문자열 부분에 대해 정의어 파싱
    const defParts = refParts.flatMap((part, refIndex) => {
      if (typeof part === "string") {
        return parseDefinitions(part).map((defPart, defIndex) => ({
          key: `ref${refIndex}-def${defIndex}`,
          content: defPart,
        }));
      }
      return [{ key: `ref${refIndex}`, content: part }];
    });

    // 2.5단계: Note 참조 스타일링
    const noteParts = defParts.flatMap(({ key, content }, idx) => {
      if (typeof content === "string") {
        return parseNotes(content).map((notePart, noteIdx) => ({
          key: `${key}-note${noteIdx}`,
          content: notePart,
        }));
      }
      return [{ key: `${key}-note${idx}`, content }];
    });

    // 3단계: 검색어 하이라이트
    const highlightParts = noteParts.flatMap(({ key, content }, idx) => {
      if (typeof content === "string") {
        return parseHighlight(content, highlight).map((hlPart, hlIdx) => ({
          key: `${key}-hl${hlIdx}`,
          content: hlPart,
        }));
      }
      return [{ key: `${key}-hl${idx}`, content }];
    });

    // 4단계: 남은 문자열에 EquationRenderer 적용
    return highlightParts.map(({ key, content }) => {
      if (typeof content === "string") {
        return <EquationRenderer key={key} text={content} />;
      }
      return <Fragment key={key}>{content}</Fragment>;
    });
  }, [text, highlight]);

  return <>{rendered}</>;
}
