"use client";

import { useState, useMemo, Fragment } from "react";
import Link from "next/link";
import tablesData from "../../../public/data/part9_tables.json";

interface TableData {
  title: string;
  page: number;
  rows: number;
  cols: number;
  html: string;
}

const tables = tablesData as Record<string, TableData>;

interface CrossReferenceLinkProps {
  text: string;
}

// 참조 패턴 정의
const REFERENCE_PATTERNS = [
  // Table 참조 (팝업)
  {
    pattern: /Table\s+(9\.\d+\.\d+\.\d+(?:\.-[A-Z])?\.?)/g,
    type: "table" as const,
  },
  // Article 참조
  {
    pattern: /Article[s]?\s+(\d+\.\d+\.\d+\.\d+\.?)/g,
    type: "article" as const,
  },
  // Sentence 참조
  {
    pattern: /Sentence[s]?\s+(\d+\.\d+\.\d+\.\d+\.\(\d+\))/g,
    type: "sentence" as const,
  },
  // Subsection 참조
  {
    pattern: /Subsection\s+(\d+\.\d+\.\d+\.?)/g,
    type: "subsection" as const,
  },
  // Section 참조
  {
    pattern: /Section\s+(\d+\.\d+\.\d+\.?)/g,
    type: "section" as const,
  },
  // Clause 참조
  {
    pattern: /Clause\s+(\d+\.\d+\.\d+\.\d+\.\(\d+\)\([a-z]\))/g,
    type: "clause" as const,
  },
  // Part 참조 (Part 9만 링크)
  {
    pattern: /Part\s+(9)\b/g,
    type: "part" as const,
  },
];

// ID를 URL 경로로 변환
function refToPath(ref: string, type: string): string | null {
  // 숫자만 추출 (예: 9.23.4.1. -> 9.23.4)
  const cleaned = ref.replace(/\.$/, "").trim();

  // Part 9 참조
  if (type === "part" && ref === "9") {
    return "/";
  }

  // 9.X.X 형태로 변환 (subsection 레벨)
  const parts = cleaned.split(".");
  if (parts.length >= 3 && parts[0] === "9") {
    const subsectionId = `${parts[0]}.${parts[1]}.${parts[2]}`;
    return `/code/${subsectionId}`;
  }

  // Part 9 외의 참조는 링크 안 함
  if (parts[0] !== "9") {
    return null;
  }

  return null;
}

// Table ID 정규화
function normalizeTableId(id: string): string {
  return "Table " + id.replace(/\.$/, "").trim();
}

// 테이블 팝업 컴포넌트
function TablePopup({
  tableId,
  isOpen,
  onClose
}: {
  tableId: string;
  isOpen: boolean;
  onClose: () => void;
}) {
  const normalizedId = normalizeTableId(tableId);
  const tableData = tables[normalizedId];

  if (!isOpen) return null;

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/50"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-lg shadow-xl max-w-4xl max-h-[90vh] overflow-auto"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-white border-b px-4 py-3 flex items-center justify-between">
          <h3 className="font-bold text-gray-900">{normalizedId}</h3>
          <button
            onClick={onClose}
            className="text-gray-500 hover:text-gray-700 text-xl font-bold px-2"
          >
            ×
          </button>
        </div>

        <div className="p-4">
          {tableData ? (
            <div
              className="obc-table-container"
              dangerouslySetInnerHTML={{ __html: tableData.html }}
            />
          ) : (
            <p className="text-yellow-600">Table not found: {normalizedId}</p>
          )}
        </div>
      </div>
    </div>
  );
}

// 테이블 링크 버튼
function TableLink({ tableId, children }: { tableId: string; children: React.ReactNode }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <>
      <button
        onClick={() => setIsOpen(true)}
        className="text-blue-600 hover:underline cursor-pointer"
      >
        {children}
      </button>
      <TablePopup
        tableId={tableId}
        isOpen={isOpen}
        onClose={() => setIsOpen(false)}
      />
    </>
  );
}

// 섹션 링크
function SectionLink({ href, children }: { href: string; children: React.ReactNode }) {
  return (
    <Link
      href={href}
      className="text-blue-600 hover:underline"
    >
      {children}
    </Link>
  );
}

// 텍스트를 파싱하여 참조를 링크로 변환
function parseReferences(text: string): React.ReactNode[] {
  // 모든 매칭을 찾아서 위치와 함께 저장
  const matches: Array<{
    start: number;
    end: number;
    fullMatch: string;
    ref: string;
    type: string;
  }> = [];

  for (const { pattern, type } of REFERENCE_PATTERNS) {
    // 패턴을 새로 생성 (lastIndex 리셋)
    const regex = new RegExp(pattern.source, pattern.flags);
    let match;

    while ((match = regex.exec(text)) !== null) {
      matches.push({
        start: match.index,
        end: match.index + match[0].length,
        fullMatch: match[0],
        ref: match[1],
        type,
      });
    }
  }

  // 시작 위치로 정렬
  matches.sort((a, b) => a.start - b.start);

  // 겹치는 매칭 제거 (먼저 나온 것 우선)
  const filteredMatches: typeof matches = [];
  let lastEnd = 0;

  for (const match of matches) {
    if (match.start >= lastEnd) {
      filteredMatches.push(match);
      lastEnd = match.end;
    }
  }

  // 결과 생성
  const result: React.ReactNode[] = [];
  let currentIndex = 0;

  for (let i = 0; i < filteredMatches.length; i++) {
    const match = filteredMatches[i];

    // 매칭 전 텍스트
    if (match.start > currentIndex) {
      result.push(text.slice(currentIndex, match.start));
    }

    // 매칭된 참조를 링크로 변환
    if (match.type === "table") {
      result.push(
        <TableLink key={`ref-${i}`} tableId={match.ref}>
          {match.fullMatch}
        </TableLink>
      );
    } else {
      const path = refToPath(match.ref, match.type);
      if (path) {
        result.push(
          <SectionLink key={`ref-${i}`} href={path}>
            {match.fullMatch}
          </SectionLink>
        );
      } else {
        // 링크 없이 텍스트만
        result.push(match.fullMatch);
      }
    }

    currentIndex = match.end;
  }

  // 마지막 텍스트
  if (currentIndex < text.length) {
    result.push(text.slice(currentIndex));
  }

  return result.length > 0 ? result : [text];
}

export default function CrossReferenceLink({ text }: CrossReferenceLinkProps) {
  const rendered = useMemo(() => {
    if (!text) return null;
    return parseReferences(text);
  }, [text]);

  return <>{rendered}</>;
}

// 유틸리티 함수 export
export { parseReferences, refToPath, TablePopup };
