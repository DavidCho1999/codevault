"use client";

import { useState, useRef, useEffect } from "react";
import { definitionMap, Definition } from "../../data/definitions";

interface DefinitionTooltipProps {
  term: string;
  children: React.ReactNode;
}

export default function DefinitionTooltip({ term, children }: DefinitionTooltipProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [position, setPosition] = useState<"top" | "bottom">("bottom");
  const triggerRef = useRef<HTMLSpanElement>(null);
  const tooltipRef = useRef<HTMLSpanElement>(null);

  // 정의어 찾기 (대소문자 무시)
  const definition = definitionMap.get(term.toLowerCase());

  useEffect(() => {
    if (isOpen && triggerRef.current && tooltipRef.current) {
      const triggerRect = triggerRef.current.getBoundingClientRect();
      const tooltipRect = tooltipRef.current.getBoundingClientRect();

      // 화면 위쪽 공간이 부족하면 아래에 표시
      if (triggerRect.top < tooltipRect.height + 10) {
        setPosition("bottom");
      } else {
        setPosition("top");
      }
    }
  }, [isOpen]);

  if (!definition) {
    // 정의어가 없으면 이탤릭체만 적용
    return <span className="italic">{children}</span>;
  }

  return (
    <span className="relative inline">
      <span
        ref={triggerRef}
        className="italic text-blue-700 cursor-help hover:underline hover:decoration-dotted"
        onMouseEnter={() => setIsOpen(true)}
        onMouseLeave={() => setIsOpen(false)}
      >
        {children}
      </span>

      {isOpen && (
        <span
          ref={tooltipRef}
          className={`absolute z-50 w-72 p-3 bg-gray-900 text-white text-sm rounded-lg shadow-lg block
            ${position === "top" ? "bottom-full mb-2" : "top-full mt-2"}
            left-1/2 -translate-x-1/2`}
        >
          {/* 화살표 */}
          <span
            className={`absolute w-3 h-3 bg-gray-900 rotate-45 left-1/2 -translate-x-1/2 block
              ${position === "top" ? "-bottom-1.5" : "-top-1.5"}`}
          />

          {/* 내용 */}
          <span className="relative block">
            <span className="font-semibold text-blue-300 mb-1 capitalize block">
              {definition.term}
            </span>
            <span className="text-gray-200 leading-relaxed block">
              {definition.definition}
            </span>
          </span>
        </span>
      )}
    </span>
  );
}

/**
 * 텍스트에서 정의어를 찾아서 DefinitionTooltip으로 감싸기
 */
export function parseDefinitions(text: string): (string | React.ReactNode)[] {
  const result: (string | React.ReactNode)[] = [];

  // 모든 정의어 패턴 생성
  const allTerms: string[] = [];
  definitionMap.forEach((_, key) => {
    allTerms.push(key);
  });

  // 긴 용어부터 매칭하도록 정렬 (e.g., "fire separation" before "fire")
  allTerms.sort((a, b) => b.length - a.length);

  // 정규식 특수문자 이스케이프
  const escaped = allTerms.map((term) =>
    term.replace(/[.*+?^${}()|[\]\\]/g, "\\$&")
  );

  // 단어 경계로 매칭 (대소문자 무시)
  const pattern = new RegExp(`\\b(${escaped.join("|")})\\b`, "gi");

  let lastIndex = 0;
  let match;
  let keyIndex = 0;

  while ((match = pattern.exec(text)) !== null) {
    // 매칭 이전 텍스트
    if (match.index > lastIndex) {
      result.push(text.slice(lastIndex, match.index));
    }

    // 매칭된 정의어를 툴팁으로 감싸기
    const matchedTerm = match[1];
    result.push(
      <DefinitionTooltip key={`def-${keyIndex++}`} term={matchedTerm}>
        {matchedTerm}
      </DefinitionTooltip>
    );

    lastIndex = pattern.lastIndex;
  }

  // 남은 텍스트
  if (lastIndex < text.length) {
    result.push(text.slice(lastIndex));
  }

  return result.length > 0 ? result : [text];
}
