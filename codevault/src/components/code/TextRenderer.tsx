"use client";

import { useMemo, Fragment } from "react";
import EquationRenderer from "./EquationRenderer";
import CrossReferenceLink, { parseReferences } from "./CrossReferenceLink";

interface TextRendererProps {
  text: string;
}

/**
 * 텍스트를 렌더링하며 다음을 처리:
 * 1. Cross-Reference 링크 (Article, Table 등)
 * 2. 수식 렌더링 (온도, 단위 등)
 */
export default function TextRenderer({ text }: TextRendererProps) {
  const rendered = useMemo(() => {
    if (!text) return null;

    // 먼저 참조를 파싱
    const parts = parseReferences(text);

    // 각 부분을 처리
    return parts.map((part, index) => {
      // 문자열인 경우 EquationRenderer로 처리
      if (typeof part === "string") {
        return <EquationRenderer key={index} text={part} />;
      }
      // 이미 React 노드인 경우 (링크 등) 그대로 반환
      return <Fragment key={index}>{part}</Fragment>;
    });
  }, [text]);

  return <>{rendered}</>;
}
