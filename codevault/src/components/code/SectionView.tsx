"use client";

import { useMemo, useEffect, useState } from "react";

import tablesData from "../../../public/data/part9_tables.json";
import TextRenderer from "./TextRenderer";
import { HighlightProvider } from "./HighlightContext";
import { useRecentSections } from "@/lib/useRecentSections";

// Inline SVG icons
const LinkIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1" />
  </svg>
);

const CheckIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
  </svg>
);

const CopyIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M8 8V5.2C8 4.08 8 3.52 8.218 3.092A2 2 0 019.092 2.218C9.52 2 10.08 2 11.2 2H18.8C19.92 2 20.48 2 20.908 2.218a2 2 0 01.874.874C22 3.52 22 4.08 22 5.2V12.8c0 1.12 0 1.68-.218 2.108a2 2 0 01-.874.874C20.48 16 19.92 16 18.8 16H16M5.2 22H12.8c1.12 0 1.68 0 2.108-.218a2 2 0 00.874-.874C16 20.48 16 19.92 16 18.8V11.2c0-1.12 0-1.68-.218-2.108a2 2 0 00-.874-.874C14.48 8 13.92 8 12.8 8H5.2C4.08 8 3.52 8 3.092 8.218a2 2 0 00-.874.874C2 9.52 2 10.08 2 11.2V18.8c0 1.12 0 1.68.218 2.108a2 2 0 00.874.874C3.52 22 4.08 22 5.2 22z" />
  </svg>
);

const PrintIcon = () => (
  <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M18 8V5c0-.552-.448-1-1-1H7c-.552 0-1 .448-1 1v3M18 18h2c1.105 0 2-.895 2-2v-6c0-1.105-.895-2-2-2H4c-1.105 0-2 .895-2 2v6c0 1.105.895 2 2 2h2M7 21h10c.552 0 1-.448 1-1v-5c0-.552-.448-1-1-1H7c-.552 0-1 .448-1 1v5c0 .552.448 1 1 1z" />
  </svg>
);

/**
 * 복사 가능한 섹션 wrapper - hover 시 액션 버튼 그룹 표시
 */
function CopyableSection({
  id,
  children,
  className = "",
}: {
  id: string;
  children: React.ReactNode;
  className?: string;
}) {
  const [copiedLink, setCopiedLink] = useState(false);
  const [copiedText, setCopiedText] = useState(false);

  const handleCopyLink = async () => {
    const url = `${window.location.origin}${window.location.pathname}#${id}`;
    try {
      await navigator.clipboard.writeText(url);
      setCopiedLink(true);
      setTimeout(() => setCopiedLink(false), 2000);
    } catch (err) {
      console.error("Failed to copy link:", err);
    }
  };

  const handleCopyText = async () => {
    const element = document.getElementById(id);
    if (element) {
      const text = element.innerText || element.textContent || "";
      try {
        await navigator.clipboard.writeText(text);
        setCopiedText(true);
        setTimeout(() => setCopiedText(false), 2000);
      } catch (err) {
        console.error("Failed to copy text:", err);
      }
    }
  };

  const handlePrintSection = () => {
    const element = document.getElementById(id);
    if (element) {
      const printWindow = window.open("", "_blank");
      if (printWindow) {
        printWindow.document.write(`
          <!DOCTYPE html>
          <html>
          <head>
            <title>Print - ${id}</title>
            <style>
              body { font-family: system-ui, -apple-system, sans-serif; padding: 2rem; max-width: 800px; margin: 0 auto; }
              h1, h2, h3 { color: #1a1a1a; }
              p { line-height: 1.6; color: #333; }
            </style>
          </head>
          <body>${element.outerHTML}</body>
          </html>
        `);
        printWindow.document.close();
        printWindow.print();
      }
    }
  };

  return (
    <div
      id={id}
      className={`group relative transition-colors duration-200 rounded-lg -mx-3 px-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 ${className}`}
    >
      {children}
      {/* Floating Action Buttons - UpCodes 스타일 */}
      <div className="absolute -right-2 top-0 flex items-center gap-0.5 p-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none group-hover:pointer-events-auto">
        {/* 텍스트 복사 */}
        <button
          onClick={handleCopyText}
          className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
          title="텍스트 복사"
        >
          {copiedText ? (
            <span className="text-green-600"><CheckIcon /></span>
          ) : (
            <span className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"><CopyIcon /></span>
          )}
        </button>
        {/* 링크 복사 */}
        <button
          onClick={handleCopyLink}
          className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
          title="링크 복사"
        >
          {copiedLink ? (
            <span className="text-green-600"><CheckIcon /></span>
          ) : (
            <span className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"><LinkIcon /></span>
          )}
        </button>
        {/* 섹션 인쇄 */}
        <button
          onClick={handlePrintSection}
          className="p-1.5 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-md transition-colors"
          title="이 섹션 인쇄"
        >
          <span className="text-gray-500 hover:text-gray-700 dark:text-gray-400 dark:hover:text-gray-200"><PrintIcon /></span>
        </button>
      </div>
    </div>
  );
}

interface EquationData {
  formula: string;
  description?: string;
  page?: number;
  insertAfter?: string;
}

interface SectionViewProps {
  id: string;
  title: string;
  content: string;
  highlight?: string;
  equations?: Record<string, EquationData>;
}

interface TableData {
  title: string;
  page: number;
  rows: number;
  cols: number;
  html: string;
}

const tables = tablesData as Record<string, TableData>;

function normalizeTableId(id: string): string {
  return id.replace(/\.$/, "").trim();
}

function TableHTML({ tableId, subtitle }: { tableId: string; subtitle?: string }) {
  const normalizedId = normalizeTableId(tableId);
  const tableData = tables[normalizedId];

  if (!tableData) {
    return (
      <div className="my-6 p-4 border border-yellow-300 dark:border-yellow-600 bg-yellow-50 dark:bg-yellow-900/30 rounded">
        <p className="text-yellow-800 dark:text-yellow-200">Table not found: {tableId}</p>
      </div>
    );
  }

  return (
    <div className="my-6 overflow-x-auto">
      <div className="mb-3 text-center">
        <p className="font-bold text-gray-900 dark:text-gray-100">{tableData.title}</p>
        {subtitle && <p className="text-sm text-gray-600 dark:text-gray-400">{subtitle}</p>}
      </div>
      <div
        className="obc-table-container"
        dangerouslySetInnerHTML={{ __html: tableData.html }}
      />
    </div>
  );
}

export default function SectionView({ id, title, content, highlight, equations }: SectionViewProps) {
  const { addSection } = useRecentSections();

  // 섹션 방문 기록
  useEffect(() => {
    if (id && title) {
      addSection(id, title);
    }
  }, [id, title, addSection]);

  // Hash 스크롤 처리
  useEffect(() => {
    const hash = window.location.hash.slice(1); // # 제거
    if (hash) {
      setTimeout(() => {
        const element = document.getElementById(hash);
        if (element) {
          element.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }, 100);
    }
  }, [content]);

  // 키보드 네비게이션 (↑/↓)
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      // input, textarea 등에서는 무시
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) {
        return;
      }

      const scrollAmount = 150;

      if (e.key === "ArrowDown") {
        e.preventDefault();
        window.scrollBy({ top: scrollAmount, behavior: "smooth" });
      } else if (e.key === "ArrowUp") {
        e.preventDefault();
        window.scrollBy({ top: -scrollAmount, behavior: "smooth" });
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, []);

  const formattedContent = useMemo(() => {
    if (!content) return null;

    // equations 삽입: "insertAfter" 패턴 다음에 수식 추가
    let processedContent = content;
    if (equations) {
      for (const [eqId, eqData] of Object.entries(equations)) {
        if (eqData.insertAfter && eqData.formula) {
          const pattern = eqData.insertAfter;
          // 패턴 다음 줄에 수식 삽입
          const replacement = `${pattern}\n${eqData.formula}`;
          processedContent = processedContent.replace(pattern, replacement);
        }
      }
    }

    const lines = processedContent.split("\n").filter((line) => line.trim());
    const result: React.ReactNode[] = [];
    const renderedTables = new Set<string>();
    let i = 0;

    while (i < lines.length) {
      const line = lines[i];
      const trimmed = line.trim();

      // 현재 섹션 ID와 동일한 제목이면 스킵 (중복 방지)
      const sectionTitleMatch = trimmed.match(/^(\d+\.\d+\.\d+\.?)\s+(.*)$/);
      if (sectionTitleMatch) {
        const lineId = sectionTitleMatch[1].replace(/\.$/, "");
        if (lineId === id) {
          i++;
          continue;
        }
      }

      // 테이블 매칭 - trailing dot optional
      const tableStartMatch = trimmed.match(/^Table\s+(9\.\d+\.\d+\.\d+)(\.-[A-G])?\.?\s*(.*)/);
      if (tableStartMatch) {
        const tableNum = tableStartMatch[1];
        const tableSuffix = tableStartMatch[2] || "";
        const tableId = "Table " + tableNum + tableSuffix;
        let subtitle = "";
        i++;

        // 이미 렌더링된 테이블이면 스킵
        if (renderedTables.has(tableId)) {
          while (i < lines.length) {
            const nextLine = lines[i].trim();
            if (nextLine.startsWith("Notes to Table")) {
              i++;
              break;
            }
            if (nextLine.match(/^(\d+\.\d+\.\d+\.\d*)\s/) && !nextLine.startsWith("Table")) break;
            if (nextLine.match(/^Table\s+\d+\.\d+\.\d+/)) break;
            i++;
          }
          continue;
        }

        renderedTables.add(tableId);

        while (i < lines.length) {
          const nextLine = lines[i].trim();
          if (nextLine.includes("Forming Part of")) {
            subtitle = nextLine;
            i++;
            continue;
          }
          if (nextLine.startsWith("Notes to Table")) {
            i++;
            break;
          }
          if (nextLine.match(/^(\d+\.\d+\.\d+\.\d*)\s/) && !nextLine.startsWith("Table")) break;
          if (nextLine.match(/^Table\s+\d+\.\d+\.\d+/)) break;
          i++;
        }

        result.push(
          <TableHTML key={"table-" + tableId + "-" + i} tableId={tableId} subtitle={subtitle} />
        );
        continue;
      }

      const articleMatch = trimmed.match(/^(\d+\.\d+\.\d+\.\d+\.)\s*(.*)$/);
      if (articleMatch) {
        const articleId = articleMatch[1].replace(/\.$/, ""); // 마지막 . 제거
        const articleContent: React.ReactNode[] = [];
        const startIndex = i;
        i++;

        // Article 아래의 모든 콘텐츠 수집 (다음 Article/Subsection/Table 전까지)
        while (i < lines.length) {
          const nextLine = lines[i].trim();

          // 다음 Article이나 Subsection이면 중단
          if (nextLine.match(/^(\d+\.\d+\.\d+\.\d+\.)\s/) ||
              (nextLine.match(/^(\d+\.\d+\.\d+\.)\s/) && !nextLine.includes("("))) {
            break;
          }
          // 테이블이면 중단
          if (nextLine.match(/^Table\s+\d+\.\d+\.\d+/)) {
            break;
          }

          // (1), (2), ... 숫자 조항
          const clauseMatch = nextLine.match(/^\((\d+)\)\s*(.*)$/);
          if (clauseMatch) {
            articleContent.push(
              <div key={`clause-${i}`} className="my-4 flex gap-2 text-base leading-relaxed text-gray-800 dark:text-gray-200">
                <span className="shrink-0 font-medium text-blue-600 dark:text-blue-400">({clauseMatch[1]})</span>
                <span><TextRenderer text={clauseMatch[2]} /></span>
              </div>
            );
            i++;
            continue;
          }

          // (a), (b), ... 알파벳 하위조항
          const subclauseMatch = nextLine.match(/^\(([a-z])\)\s*(.*)$/);
          if (subclauseMatch) {
            articleContent.push(
              <div key={`subclause-${i}`} className="my-2 flex gap-2 text-gray-600 dark:text-gray-400 text-sm ml-8">
                <span className="shrink-0 text-gray-500 dark:text-gray-500">({subclauseMatch[1]})</span>
                <span><TextRenderer text={subclauseMatch[2]} /></span>
              </div>
            );
            i++;
            continue;
          }

          // (i), (ii), ... 로마숫자 하위조항
          const romanMatch = nextLine.match(/^\((i{1,3}|iv|v|vi{0,3})\)\s*(.*)$/);
          if (romanMatch) {
            articleContent.push(
              <div key={`roman-${i}`} className="my-1 flex gap-2 text-gray-600 dark:text-gray-400 text-sm ml-16">
                <span className="shrink-0 text-gray-400 dark:text-gray-500">({romanMatch[1]})</span>
                <span><TextRenderer text={romanMatch[2]} /></span>
              </div>
            );
            i++;
            continue;
          }

          // Notes to Table
          const notesToTableMatch = nextLine.match(/^Notes?\s+to\s+Table\s+([\d.]+[A-G]?):?\s*(.*)$/i);
          if (notesToTableMatch) {
            articleContent.push(
              <div key={`notes-${i}`} className="my-4 p-3 bg-amber-50 dark:bg-amber-900/30 border-l-4 border-amber-400 dark:border-amber-600 rounded-r">
                <p className="text-sm font-semibold text-amber-800 dark:text-amber-300">
                  📝 Notes to Table {notesToTableMatch[1]}
                </p>
                {notesToTableMatch[2] && (
                  <p className="text-sm text-amber-700 dark:text-amber-400 mt-1">
                    <TextRenderer text={notesToTableMatch[2]} />
                  </p>
                )}
              </div>
            );
            i++;
            continue;
          }

          // 수식 라인 감지 (예: S = CbSs + Sr, Do = 10(Ho – 0.8 Ss / γ))
          const equationMatch = nextLine.match(/^([A-Za-z][a-z]?\s*=\s*[^,]+)$/);
          if (equationMatch && nextLine.length < 80 && /[=\+\-\/\*\(\)]/.test(nextLine)) {
            articleContent.push(
              <div key={`eq-${i}`} className="obc-equation">
                <TextRenderer text={nextLine} />
              </div>
            );
            i++;
            continue;
          }

          // "where" 블록 시작 감지
          if (nextLine.toLowerCase() === "where") {
            const whereContent: React.ReactNode[] = [];
            i++;

            // where 블록 내용 수집 (변수 정의들)
            while (i < lines.length) {
              const varLine = lines[i].trim();
              // 변수 정의 패턴: "Cb = ..." 또는 "  Cb = ..."
              const varMatch = varLine.match(/^([A-Za-z][a-z0-9]*)\s*=\s*(.+)$/);
              if (varMatch) {
                whereContent.push(
                  <span key={`var-${i}`} className="where-var">
                    <span className="where-var-name">{varMatch[1]}</span> = {varMatch[2]}
                  </span>
                );
                i++;
                continue;
              }
              // 빈 줄이거나 다른 패턴이면 where 블록 종료
              if (!varLine || varLine.match(/^[\(\d]/) || varLine.match(/^\d+\.\d+/)) {
                break;
              }
              // 일반 설명 텍스트
              whereContent.push(
                <span key={`where-text-${i}`} className="block text-gray-600 dark:text-gray-400 ml-4">
                  {varLine}
                </span>
              );
              i++;
            }

            if (whereContent.length > 0) {
              articleContent.push(
                <div key={`where-${i}`} className="obc-where-block">
                  <div className="where-title">where</div>
                  {whereContent}
                </div>
              );
            }
            continue;
          }

          // 일반 텍스트
          if (nextLine) {
            articleContent.push(
              <p key={`text-${i}`} className="my-2 text-gray-700 dark:text-gray-300">
                <TextRenderer text={nextLine} />
              </p>
            );
          }
          i++;
        }

        result.push(
          <CopyableSection
            key={startIndex}
            id={articleId}
            className="mt-6 first:mt-0 py-2"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              <span className="font-mono text-blue-600 dark:text-blue-400 mr-2">{articleMatch[1]}</span>
              {articleMatch[2]}
            </h3>
            {articleContent}
          </CopyableSection>
        );
        continue;
      }

      const subsectionMatch = trimmed.match(/^(\d+\.\d+\.\d+\.)\s*(.*)$/);
      if (subsectionMatch && !trimmed.includes("(")) {
        const subsectionId = subsectionMatch[1].replace(/\.$/, ""); // 마지막 . 제거
        result.push(
          <CopyableSection
            key={i}
            id={subsectionId}
            className="mt-8 first:mt-0 border-t dark:border-gray-700 pt-6"
          >
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-3">
              <span className="font-mono text-blue-600 dark:text-blue-400 mr-2">{subsectionMatch[1]}</span>
              {subsectionMatch[2]}
            </h2>
          </CopyableSection>
        );
        i++;
        continue;
      }

      const clauseMatch = trimmed.match(/^\((\d+)\)\s*(.*)$/);
      if (clauseMatch) {
        result.push(
          <div key={i} className="my-4 flex gap-2 text-base leading-relaxed text-gray-800 dark:text-gray-200">
            <span className="shrink-0 font-medium text-blue-600 dark:text-blue-400">({clauseMatch[1]})</span>
            <span><TextRenderer text={clauseMatch[2]} /></span>
          </div>
        );
        i++;
        continue;
      }

      const subclauseMatch = trimmed.match(/^\(([a-z])\)\s*(.*)$/);
      if (subclauseMatch) {
        result.push(
          <div key={i} className="my-2 flex gap-2 text-gray-600 dark:text-gray-400 text-sm ml-8">
            <span className="shrink-0 text-gray-500 dark:text-gray-500">({subclauseMatch[1]})</span>
            <span><TextRenderer text={subclauseMatch[2]} /></span>
          </div>
        );
        i++;
        continue;
      }

      const romanMatch = trimmed.match(/^\((i{1,3}|iv|v|vi{0,3})\)\s*(.*)$/);
      if (romanMatch) {
        result.push(
          <div key={i} className="my-1 flex gap-2 text-gray-600 dark:text-gray-400 text-sm ml-16">
            <span className="shrink-0 text-gray-400 dark:text-gray-500">({romanMatch[1]})</span>
            <span><TextRenderer text={romanMatch[2]} /></span>
          </div>
        );
        i++;
        continue;
      }

      // Notes to Table 스타일링
      const notesToTableMatch = trimmed.match(/^Notes?\s+to\s+Table\s+([\d.]+[A-G]?):?\s*(.*)$/i);
      if (notesToTableMatch) {
        result.push(
          <div key={i} className="my-4 p-3 bg-amber-50 dark:bg-amber-900/30 border-l-4 border-amber-400 dark:border-amber-600 rounded-r">
            <p className="text-sm font-semibold text-amber-800 dark:text-amber-300">
              📝 Notes to Table {notesToTableMatch[1]}
            </p>
            {notesToTableMatch[2] && (
              <p className="text-sm text-amber-700 dark:text-amber-400 mt-1">
                <TextRenderer text={notesToTableMatch[2]} />
              </p>
            )}
          </div>
        );
        i++;
        continue;
      }

      // 수식 라인 감지 (Article 바깥)
      const equationMatch = trimmed.match(/^([A-Za-z][a-z]?\s*=\s*[^,]+)$/);
      if (equationMatch && trimmed.length < 80 && /[=\+\-\/\*\(\)]/.test(trimmed)) {
        result.push(
          <div key={i} className="obc-equation">
            <TextRenderer text={trimmed} />
          </div>
        );
        i++;
        continue;
      }

      // "where" 블록 시작 감지 (Article 바깥)
      if (trimmed.toLowerCase() === "where") {
        const whereContent: React.ReactNode[] = [];
        i++;

        while (i < lines.length) {
          const varLine = lines[i].trim();
          const varMatch = varLine.match(/^([A-Za-z][a-z0-9]*)\s*=\s*(.+)$/);
          if (varMatch) {
            whereContent.push(
              <span key={`var-${i}`} className="where-var">
                <span className="where-var-name">{varMatch[1]}</span> = {varMatch[2]}
              </span>
            );
            i++;
            continue;
          }
          if (!varLine || varLine.match(/^[\(\d]/) || varLine.match(/^\d+\.\d+/)) {
            break;
          }
          whereContent.push(
            <span key={`where-text-${i}`} className="block text-gray-600 dark:text-gray-400 ml-4">
              {varLine}
            </span>
          );
          i++;
        }

        if (whereContent.length > 0) {
          result.push(
            <div key={`where-${i}`} className="obc-where-block">
              <div className="where-title">where</div>
              {whereContent}
            </div>
          );
        }
        continue;
      }

      if (trimmed) {
        result.push(
          <p key={i} className="my-2 text-gray-700 dark:text-gray-300"><TextRenderer text={trimmed} /></p>
        );
      }
      i++;
    }

    return result;
  }, [content, equations]);

  return (
    <HighlightProvider highlight={highlight || null}>
      <article className="max-w-4xl">
        <header className="mb-6 pb-4 border-b border-gray-200 dark:border-gray-700 bg-blue-50 dark:bg-blue-900/20 border-l-4 border-l-blue-400 dark:border-l-blue-500 -mx-4 px-4 py-4 rounded-r-lg">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            <span className="font-mono text-blue-600 dark:text-blue-400 mr-2">{id}</span>
            {title}
          </h1>
        </header>

        {content ? (
          <div className="prose prose-gray dark:prose-invert max-w-none">{formattedContent}</div>
        ) : (
          <p className="text-gray-500 dark:text-gray-400 italic">No content available for this section.</p>
        )}
      </article>
    </HighlightProvider>
  );
}
