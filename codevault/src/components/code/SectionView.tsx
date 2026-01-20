"use client";

import { useMemo, useEffect, useState, useRef } from "react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeRaw from "rehype-raw";
import rehypeKatex from "rehype-katex";
import "katex/dist/katex.min.css";

import tablesData from "../../../public/data/part9_tables.json";
import TextRenderer from "./TextRenderer";
import { HighlightProvider } from "./HighlightContext";
import { useRecentSections } from "@/lib/useRecentSections";
import { useActiveSection } from "@/lib/ActiveSectionContext";

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

  return (
    <div
      id={id}
      className={`group relative transition-colors duration-200 rounded-lg -mx-3 px-3 hover:bg-gray-50 dark:hover:bg-gray-800/50 ${className}`}
    >
      {children}
      {/* Floating Action Buttons - 섹션 위에 표시 */}
      <div className="absolute right-0 -top-8 flex items-center gap-0.5 p-1 rounded-lg border border-gray-200 dark:border-gray-700 bg-white dark:bg-gray-800 shadow-sm opacity-0 group-hover:opacity-100 transition-opacity duration-150 pointer-events-none group-hover:pointer-events-auto">
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
  tables?: Record<string, string>; // DB에서 온 테이블 HTML (tableId → html)
  content_format?: string; // "markdown" for Part 10+
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

function TableHTML({ tableId, subtitle, dbTables }: { tableId: string; subtitle?: string; dbTables?: Record<string, string> }) {
  const normalizedId = normalizeTableId(tableId);

  // DB 테이블 우선, 없으면 JSON fallback
  const dbHtml = dbTables?.[normalizedId];
  const tableData = tables[normalizedId];
  const html = dbHtml || tableData?.html;
  const title = tableData?.title || normalizedId;

  if (!html) {
    return (
      <div className="my-6 p-4 border border-yellow-300 dark:border-yellow-600 bg-yellow-50 dark:bg-yellow-900/30 rounded">
        <p className="text-yellow-800 dark:text-yellow-200">Table not found: {tableId}</p>
      </div>
    );
  }

  return (
    <div className="my-6 mb-2 overflow-x-auto">
      <div className="mb-3 text-center">
        <p className="font-bold text-gray-900 dark:text-gray-100">{title}</p>
        {subtitle && <p className="text-sm text-gray-600 dark:text-gray-400">{subtitle}</p>}
      </div>
      <div
        className="obc-table-container"
        dangerouslySetInnerHTML={{ __html: html }}
      />
    </div>
  );
}

export default function SectionView({ id, title, content, highlight, equations, tables: propTables, content_format }: SectionViewProps) {
  const { addSection } = useRecentSections();
  const { setActiveSection } = useActiveSection();
  const containerRef = useRef<HTMLDivElement>(null);

  // 섹션 방문 기록
  useEffect(() => {
    if (id && title) {
      addSection(id, title);
    }
  }, [id, title, addSection]);

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

  // Intersection Observer로 현재 보이는 섹션 감지
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    // 모든 관찰 대상 요소와 위치 추적
    let visibleSections = new Map<string, number>();

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            // 보이는 섹션의 top 위치 저장
            visibleSections.set(entry.target.id, entry.boundingClientRect.top);
          } else {
            // 안 보이면 제거
            visibleSections.delete(entry.target.id);
          }
        });

        // 화면 상단에 가장 가까운 섹션 선택
        if (visibleSections.size > 0) {
          let closestId = "";
          let closestTop = Infinity;
          visibleSections.forEach((top, id) => {
            if (top >= 0 && top < closestTop) {
              closestTop = top;
              closestId = id;
            }
          });
          // 모든 섹션이 화면 위로 지나갔으면 가장 아래 섹션 선택
          if (!closestId) {
            visibleSections.forEach((top, id) => {
              if (Math.abs(top) < Math.abs(closestTop)) {
                closestTop = top;
                closestId = id;
              }
            });
          }
          if (closestId) {
            setActiveSection(closestId);
          }
        }
      },
      {
        rootMargin: "0px 0px -60% 0px", // 화면 상단 40% 영역에서 감지
        threshold: 0,
      }
    );

    // Subsection과 Article 요소들 관찰
    const sections = container.querySelectorAll("[id^='9.']");
    sections.forEach((section) => observer.observe(section));

    return () => {
      observer.disconnect();
      visibleSections.clear();
    };
  }, [content, setActiveSection]);

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

    // 실수 #4 해결: 소문자로 시작하는 줄을 이전 줄에 연결
    // (a), (1), 9.x.x, 대문자로 시작하는 줄은 유지, 그 외 소문자 시작 줄은 공백으로 연결
    // 단, "where" 키워드, 수식 패턴(xd = ..., γ = ...), [SECTION:...], [ARTICLE:...], [SUBSECTION:...] 마커, 모든 HTML 태그, 마크다운 헤딩/볼드/이탤릭, 마크다운 리스트(-) 앞의 줄바꿈은 유지
    // 추가: **(N) 또는 *(N) 형식의 볼드/이탤릭 캡션도 유지
    // 추가: 연속된 줄바꿈(\n\n - 빈 줄)도 유지하여 마크다운 헤딩 앞의 빈 줄 보존
    processedContent = processedContent.replace(/\n(?!where\b|[a-zγ]{1,3}\s*=|\[SECTION:|\[ARTICLE:|\[SUBSECTION:|[(\d9A-Z]|<\/?[a-z]|#{2,4}\s|\*{1,2}[A-Z(]|-\s|\n)/g, ' ');

    const lines = processedContent.split("\n").filter((line) => line.trim());

    const result: React.ReactNode[] = [];
    const renderedTables = new Set<string>();
    let i = 0;

    while (i < lines.length) {
      const line = lines[i];
      const trimmed = line.trim();

      // [SECTION:id:title] 마커 처리 - Section 헤더로 렌더링 (Part 전체 뷰에서 사용)
      const sectionMarkerMatch = trimmed.match(/^\[SECTION:([^:]+):([^\]]*)\]$/);
      if (sectionMarkerMatch) {
        const sectionId = sectionMarkerMatch[1];
        const sectionTitle = sectionMarkerMatch[2];
        result.push(
          <div key={`section-${sectionId}`} id={sectionId} className="mt-12 mb-6 scroll-mt-20 border-b-2 border-gray-300 dark:border-gray-600 pb-4">
            <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
              <span className="text-gray-900 dark:text-gray-100 font-bold">{sectionId}</span>
              {sectionTitle && <span className="ml-3">{sectionTitle}</span>}
            </h2>
          </div>
        );
        i++;
        continue;
      }

      // [SUBSECTION:id:title] 마커 처리 - Subsection 헤더로 렌더링 (ml-4 들여쓰기)
      const subsectionMarkerMatch = trimmed.match(/^\[SUBSECTION:([^:]+):([^\]]*)\]$/);
      if (subsectionMarkerMatch) {
        const subsectionId = subsectionMarkerMatch[1];
        const subsectionTitle = subsectionMarkerMatch[2];
        result.push(
          <div key={`subsection-${subsectionId}`} id={subsectionId} className="mt-10 mb-4 scroll-mt-20 ml-4">
            <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">
              <span className="text-gray-900 dark:text-gray-100 font-bold">{subsectionId}</span>
              {subsectionTitle && <span className="ml-3">{subsectionTitle}</span>}
            </h2>
          </div>
        );
        i++;
        continue;
      }

      // [ARTICLE:id:title] 마커 처리 - Article 헤더로 렌더링 (ml-8 들여쓰기)
      const articleMarkerMatch = trimmed.match(/^\[ARTICLE:([^:]+):([^\]]*)\]$/);
      if (articleMarkerMatch) {
        const articleId = articleMarkerMatch[1];
        const articleTitle = articleMarkerMatch[2];
        result.push(
          <div key={`article-${articleId}`} id={articleId} className="mt-4 mb-0 scroll-mt-20 ml-8">
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
              <span className="text-gray-900 dark:text-gray-100 font-semibold">{articleId}</span>
              {articleTitle && <span className="ml-2">{articleTitle}</span>}
            </h3>
          </div>
        );
        i++;
        continue;
      }

      // ========== 통합 테이블 헤딩 처리 (Part 9, 10, 11, 12+) ==========
      // 지원 형식:
      // - Part 9: "Table 9.6.1.3.-A" (해시 없음)
      // - Part 10+: "## Table 10.3.2.2.-A", "### Table 11.2.1.1.-B(1)(4)", "#### Table 11.2.1.1.-F"
      // 캡션: **볼드** 또는 평문 (같은 줄 또는 다음 줄)
      // Forming Part: *이탤릭* 또는 평문
      const unifiedTableMatch = trimmed.match(/^(?:#{2,4}\s+)?Table\s+([\d.]+-[A-Z](?:\/[A-Z])?(?:\(\d+\))*(?:\s*\(Cont'd\))?)\s*(.*)$/);
      if (unifiedTableMatch) {
        const startIdx = i;
        const tableId = unifiedTableMatch[1];
        const sameLineRest = unifiedTableMatch[2]?.trim() || "";
        let caption = "";
        let formingPart = "";

        // 1. 같은 줄에 캡션이 있는 경우 (Part 9/10/11 스타일)
        if (sameLineRest) {
          // "Forming Part of..."가 같은 줄에 있으면 분리
          const inlineFormingMatch = sameLineRest.match(/^(.*?)\s*(Forming Part of .+)$/);
          if (inlineFormingMatch) {
            caption = inlineFormingMatch[1].trim();
            formingPart = inlineFormingMatch[2].trim();
          } else if (!sameLineRest.startsWith("Forming Part")) {
            caption = sameLineRest;
          } else {
            formingPart = sameLineRest;
          }
        }

        // 2. 다음 줄에서 캡션 찾기: **볼드** 또는 평문
        if (!caption && i + 1 < lines.length) {
          const nextLine = lines[i + 1].trim();
          // **볼드 캡션** 패턴
          const boldCaptionMatch = nextLine.match(/^\*\*(.+?)\*\*$/);
          if (boldCaptionMatch) {
            caption = boldCaptionMatch[1];
            i++;
          }
          // 평문 캡션 (Forming Part, Table, 숫자로 시작하지 않는 경우)
          else if (nextLine &&
                   !nextLine.startsWith("Forming Part") &&
                   !nextLine.startsWith("*Forming") &&
                   !nextLine.match(/^Table\s+\d/) &&
                   !nextLine.match(/^\d+\.\d+\.\d+/) &&
                   !nextLine.startsWith("<table") &&
                   !nextLine.startsWith("Notes to Table")) {
            caption = nextLine.replace(/^\*\*|\*\*$/g, ''); // 볼드 마커 제거
            i++;
          }
        }

        // 3. Forming Part 찾기 (다음 4줄 내에서)
        let searchIdx = i + 1;
        while (searchIdx < lines.length && searchIdx <= i + 4) {
          const nextLine = lines[searchIdx].trim();
          if (!nextLine) {
            searchIdx++;
            continue;
          }
          // *Forming Part of...* 패턴 (이탤릭)
          const italicFormingMatch = nextLine.match(/^\*(.+?)\*$/);
          if (italicFormingMatch && italicFormingMatch[1].includes("Forming Part")) {
            formingPart = italicFormingMatch[1];
            i = searchIdx;
            break;
          }
          // Forming Part of... 패턴 (평문)
          if (nextLine.startsWith("Forming Part of")) {
            formingPart = nextLine;
            i = searchIdx;
            break;
          }
          // <table, Table, 숫자, 마크다운 헤딩으로 시작하면 중단 (다음 테이블/섹션 시작)
          if (nextLine.startsWith("<table") ||
              nextLine.match(/^(?:#{2,4}\s+)?Table\s+\d/) ||
              nextLine.match(/^\d+\.\d+\.\d+/) ||
              nextLine.match(/^#{2,4}\s/)) {
            break;
          }
          searchIdx++;
        }

        // 이미 렌더링된 테이블이면 스킵
        const fullTableId = "Table " + tableId;
        if (renderedTables.has(fullTableId)) {
          i++;
          continue;
        }
        renderedTables.add(fullTableId);

        // 다음 줄들에 인라인 <table>이 있는지 확인 (Part 10/11 스타일)
        let hasInlineTable = false;
        for (let checkIdx = i + 1; checkIdx < Math.min(i + 6, lines.length); checkIdx++) {
          const checkLine = lines[checkIdx]?.trim();
          if (checkLine?.startsWith("<table")) {
            hasInlineTable = true;
            break;
          }
          // 다른 콘텐츠가 나오면 중단 (Article, 다른 Table 등)
          if (checkLine?.match(/^\d+\.\d+\.\d+/) || checkLine?.match(/^Table\s+\d/)) {
            break;
          }
        }

        // 테이블 헤더 + 본체 + Notes를 하나의 컨테이너로 묶기
        const tableElements: React.ReactNode[] = [];

        // 1. 헤더 추가
        tableElements.push(
          <div key="header" className="text-center mb-4">
            <p className="text-sm font-bold text-black">Table {tableId}</p>
            {caption && <p className="text-sm font-bold text-black">{caption}</p>}
            {formingPart && <p className="text-xs text-black">{formingPart}</p>}
          </div>
        );

        i++;

        // 2. 인라인 테이블 및 Notes 수집
        if (hasInlineTable) {
          while (i < lines.length) {
            const tableLine = lines[i].trim();

            // 인라인 <table> 찾기
            if (tableLine.startsWith("<table")) {
              const tableLines: string[] = [tableLine];
              if (!tableLine.includes("</table>")) {
                i++;
                while (i < lines.length) {
                  const tl = lines[i].trim();
                  tableLines.push(tl);
                  i++;
                  if (tl.includes("</table>")) break;
                }
              } else {
                i++;
              }
              tableElements.push(
                <div key={`inline-table-${i}`} className="obc-table-inner" dangerouslySetInnerHTML={{ __html: tableLines.join('\n') }} />
              );
              continue;
            }

            // Notes to Table 찾기
            const notesMatch = tableLine.match(/Notes?\s+to\s+Table\s+([\d.]+[A-Z]?(?:-[A-Z])?)/i);
            if (notesMatch || tableLine.includes("table-notes-title")) {
              const noteContent: { type: 'table' | 'item'; content: string }[] = [];
              i++;
              while (i < lines.length) {
                const nl = lines[i].trim();
                // 종료 조건: 새 테이블 헤딩, 섹션 번호
                if (!nl && i + 1 < lines.length && !lines[i + 1].trim()) break;
                if (nl.match(/^#{2,4}\s+Table/) || nl.match(/^Table\s+\d/) || nl.match(/^\d+\.\d+\.\d+\.\d+/) || nl.match(/^<h[1-4]/)) break;
                // 종료 조건: 대시 없이 (숫자)로 시작하면 일반 clause → Notes 종료
                if (nl.match(/^\(\d+\)/) && !nl.startsWith('-')) break;
                if (!nl) { i++; continue; }
                // Notes 안의 <table> 처리
                if (nl.startsWith("<table")) {
                  const tableLines = [nl];
                  if (!nl.includes('</table>')) {
                    i++;
                    while (i < lines.length) {
                      tableLines.push(lines[i]);
                      if (lines[i].includes('</table>')) break;
                      i++;
                    }
                  }
                  noteContent.push({ type: 'table', content: tableLines.join('\n') });
                  i++;
                  continue;
                }
                // - (1), - (2) 패턴만 Notes 항목으로 추가
                if (nl.startsWith("-") || nl.startsWith('•')) {
                  noteContent.push({ type: 'item', content: nl });
                }
                i++;
              }
              tableElements.push(
                <div key={`notes-${i}`} className="table-notes mt-4 p-3 bg-amber-50/50 rounded-r">
                  <p className="text-sm font-semibold text-amber-800 mb-2">Notes to Table {tableId}:</p>
                  {noteContent.map((item, idx) => (
                    item.type === 'table' ? (
                      <div key={idx} className="my-2 text-xs overflow-x-auto" dangerouslySetInnerHTML={{ __html: item.content }} />
                    ) : (
                      <p key={idx} className="text-xs text-amber-700 mt-1 ml-2">{item.content}</p>
                    )
                  ))}
                </div>
              );
              break;
            }

            // 다른 테이블이나 섹션 시작하면 종료
            if (tableLine.match(/^#{2,4}\s+Table/) || tableLine.match(/^Table\s+\d/) || tableLine.match(/^\d+\.\d+\.\d+\.\d+/)) {
              break;
            }

            i++;
          }
        } else if (propTables) {
          // Part 9 스타일 - TableHTML 컴포넌트 사용
          tableElements.push(
            <TableHTML key={`table-body-${tableId}`} tableId={fullTableId} dbTables={propTables} />
          );
        }

        // 하나의 컨테이너로 렌더링
        result.push(
          <div key={`table-container-${tableId}-${startIdx}`} className="obc-table-container my-6">
            {tableElements}
          </div>
        );

        continue;
      }

      // "Forming Part of..." 패턴 (테이블 헤딩 박스 밖에 있는 경우) - 이탤릭으로 렌더링
      const formingPartMatch = trimmed.match(/^Forming Part of\s+(.+)$/);
      if (formingPartMatch) {
        result.push(
          <p key={`forming-${i}`} className="text-sm text-gray-500 dark:text-gray-400 my-2">
            {trimmed}
          </p>
        );
        i++;
        continue;
      }

      // 현재 섹션 ID와 동일한 제목이면 스킵 (중복 방지)
      const sectionTitleMatch = trimmed.match(/^(\d+\.\d+\.\d+\.?)\s+(.*)$/);
      if (sectionTitleMatch) {
        const lineId = sectionTitleMatch[1].replace(/\.$/, "");
        if (lineId === id) {
          i++;
          continue;
        }
      }

      // NOTE: Part 9 테이블 처리가 통합 테이블 핸들러로 이동됨 (line 388)

      const articleMatch = trimmed.match(/^(\d+\.\d+\.\d+\.\d+\.)\s*(.*)$/);
      if (articleMatch) {
        const articleId = articleMatch[1].replace(/\.$/, ""); // 마지막 . 제거
        const articleContent: React.ReactNode[] = [];
        const startIndex = i;
        i++;

        // Article 아래의 모든 콘텐츠 수집 (다음 Article/Subsection/Table/마커 전까지)
        while (i < lines.length) {
          const nextLine = lines[i].trim();

          // 다음 Article이나 Subsection이면 중단
          if (nextLine.match(/^(\d+\.\d+\.\d+\.\d+\.)\s/) ||
              (nextLine.match(/^(\d+\.\d+\.\d+\.)\s/) && !nextLine.includes("("))) {
            break;
          }
          // [SECTION:...], [SUBSECTION:...], [ARTICLE:...] 마커면 중단
          if (nextLine.match(/^\[(?:SECTION|SUBSECTION|ARTICLE):/)) {
            break;
          }
          // 테이블이면 Article 내부에 포함
          const inlineTableMatch = nextLine.match(/^Table\s+(9\.\d+\.\d+\.\d+)(\.-[A-G])?\.?\s*(.*)/);
          if (inlineTableMatch) {
            const tableNum = inlineTableMatch[1];
            const tableSuffix = inlineTableMatch[2] || "";
            const inlineTableId = "Table " + tableNum + tableSuffix;
            let inlineSubtitle = "";
            i++;

            // 이미 렌더링된 테이블이면 스킵
            if (!renderedTables.has(inlineTableId)) {
              renderedTables.add(inlineTableId);

              while (i < lines.length) {
                const tableLine = lines[i].trim();
                if (tableLine.includes("Forming Part of")) {
                  inlineSubtitle = tableLine;
                  i++;
                  continue;
                }
                if (tableLine.startsWith("Notes to Table")) {
                  i++;
                  break;
                }
                if (tableLine.match(/^(\d+\.\d+\.\d+\.\d*)\s/) && !tableLine.startsWith("Table")) break;
                if (tableLine.match(/^Table\s+\d+\.\d+\.\d+/)) break;
                i++;
              }

              articleContent.push(
                <TableHTML key={"inline-table-" + inlineTableId + "-" + i} tableId={inlineTableId} subtitle={inlineSubtitle} dbTables={propTables} />
              );
            }
            continue;
          }

          // (1), (2), (3.1), ... 숫자 조항 (소수점 포함)
          const clauseMatch = nextLine.match(/^\((\d+(?:\.\d+)?)\)\s*(.*)$/);
          if (clauseMatch) {
            const clauseNum = clauseMatch[1];
            let clauseText = clauseMatch[2];
            i++;

            // 쉼표로 끝나면 정의문 → 다음 줄들을 모음 (Definitions 패턴)
            if (clauseText.trim().endsWith(',')) {
              const extraLines: string[] = [];
              while (i < lines.length) {
                const peekLine = lines[i].trim();
                // 다음 clause, subclause, article이 나오면 종료
                if (peekLine.match(/^\(\d+(?:\.\d+)?\)/) ||  // (1), (2)
                    peekLine.match(/^\([a-z]\)/) ||           // (a), (b)
                    peekLine.match(/^\((i{1,3}|iv|v|vi{0,3})\)/) || // (i), (ii)
                    peekLine.match(/^\d+\.\d+\.\d+\.\d+/) ||  // article
                    peekLine.match(/^\[ARTICLE:/)) {
                  break;
                }
                extraLines.push(peekLine);
                i++;
              }
              if (extraLines.length > 0) {
                clauseText += '\n\n' + extraLines.join('\n\n');
              }
            }

            articleContent.push(
              <div key={`clause-${i}`} className="my-2 ml-6 flex gap-2 text-sm leading-relaxed text-gray-800 dark:text-gray-200">
                <span className="shrink-0 text-black dark:text-white">({clauseNum})</span>
                <span><TextRenderer text={clauseText} /></span>
              </div>
            );
            continue;
          }

          // (a), (b), ... 알파벳 하위조항
          const subclauseMatch = nextLine.match(/^\(([a-z])\)\s*(.*)$/);
          if (subclauseMatch) {
            articleContent.push(
              <div key={`subclause-${i}`} className="my-0.5 flex gap-2 text-gray-900 dark:text-gray-100 text-sm ml-14">
                <span className="shrink-0 text-black dark:text-white">({subclauseMatch[1]})</span>
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
              <div key={`roman-${i}`} className="my-1 flex gap-2 text-gray-900 dark:text-gray-100 text-sm ml-18">
                <span className="shrink-0 text-black dark:text-white">({romanMatch[1]})</span>
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
              <div key={`notes-${i}`} className="mt-0 mb-4 p-3 bg-amber-50/50 rounded-r">
                <p className="text-sm font-semibold text-amber-800">
                  📝 Notes to Table {notesToTableMatch[1]}
                </p>
                {notesToTableMatch[2] && (
                  <p className="text-sm text-amber-700 mt-0.5">
                    <TextRenderer text={notesToTableMatch[2]} />
                  </p>
                )}
              </div>
            );
            i++;
            continue;
          }

          // 수식 라인 감지 (예: S = CbSs + Sr, Do = 10(Ho – 0.8 Ss / γ))
          // "where"로 끝나는 라인은 제외
          const equationMatch = nextLine.match(/^([A-Za-z][a-z]?\s*=\s*[^,]+)$/);
          if (equationMatch && nextLine.length < 80 && /[=\+\-\/\*\(\)]/.test(nextLine) && !/\bwhere\s*$/i.test(nextLine)) {
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

              // where 블록 종료 조건:
              // - 빈 줄
              // - (1), (2) 같은 clause 시작
              // - (a), (b) 같은 sub-clause 시작
              // - 9.4.2 같은 섹션 번호
              if (!varLine ||
                  varLine.match(/^\(\d+\)/) ||      // (1), (2), ...
                  varLine.match(/^\([a-z]\)/) ||    // (a), (b), ...
                  varLine.match(/^9\.\d+\.\d+/)) {  // 9.x.x 섹션 번호
                break;
              }

              // 변수 정의 패턴: "Cb = ...", "Ss = ...", "γ = ..."
              const varMatch = varLine.match(/^([A-Za-zγ][a-z0-9]*)\s*=\s*(.+)$/);
              if (varMatch) {
                whereContent.push(
                  <span key={`var-${i}`} className="where-var">
                    <span className="where-var-name">{varMatch[1]}</span> = {varMatch[2]}
                  </span>
                );
                i++;
                continue;
              }

              // 연속 텍스트 (0.55 for all other roofs, 등)
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
            className="mt-6 first:mt-0 py-2 ml-6"
          >
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              <span className="font-mono text-gray-900 dark:text-gray-100 font-semibold mr-2">{articleMatch[1]}</span>
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
              <span className="font-mono text-gray-900 dark:text-gray-100 font-bold mr-2">{subsectionMatch[1]}</span>
              {subsectionMatch[2]}
            </h2>
          </CopyableSection>
        );
        i++;
        continue;
      }

      // (1), (2), (3.1), ... 숫자 조항 (소수점 포함)
      const clauseMatch = trimmed.match(/^\((\d+(?:\.\d+)?)\)\s*(.*)$/);
      if (clauseMatch) {
        const clauseNum = clauseMatch[1];
        let clauseText = clauseMatch[2];
        i++;

        // 쉼표로 끝나면 정의문 → 다음 줄들을 모음 (Definitions 패턴)
        if (clauseText.trim().endsWith(',')) {
          const extraLines: string[] = [];
          while (i < lines.length) {
            const peekLine = lines[i].trim();
            // 다음 clause, subclause, article, 마커가 나오면 종료
            if (peekLine.match(/^\(\d+(?:\.\d+)?\)/) ||  // (1), (2)
                peekLine.match(/^\([a-z]\)/) ||           // (a), (b)
                peekLine.match(/^\((i{1,3}|iv|v|vi{0,3})\)/) || // (i), (ii)
                peekLine.match(/^\d+\.\d+\.\d+\.\d+/) ||  // article
                peekLine.match(/^\[(?:SECTION|SUBSECTION|ARTICLE):/)) { // 마커
              break;
            }
            extraLines.push(peekLine);
            i++;
          }
          if (extraLines.length > 0) {
            clauseText += '\n\n' + extraLines.join('\n\n');
          }
        }

        result.push(
          <div key={i} className="my-2 ml-12 flex gap-2 text-sm leading-relaxed text-gray-800 dark:text-gray-200">
            <span className="shrink-0 text-black dark:text-white">({clauseNum})</span>
            <span><TextRenderer text={clauseText} /></span>
          </div>
        );
        continue;
      }

      const subclauseMatch = trimmed.match(/^\(([a-z])\)\s*(.*)$/);
      if (subclauseMatch) {
        result.push(
          <div key={i} className="my-0.5 flex gap-2 text-gray-900 dark:text-gray-100 text-sm ml-18">
            <span className="shrink-0 text-black dark:text-white">({subclauseMatch[1]})</span>
            <span><TextRenderer text={subclauseMatch[2]} /></span>
          </div>
        );
        i++;
        continue;
      }

      const romanMatch = trimmed.match(/^\((i{1,3}|iv|v|vi{0,3})\)\s*(.*)$/);
      if (romanMatch) {
        result.push(
          <div key={i} className="my-1 flex gap-2 text-gray-900 dark:text-gray-100 text-sm ml-20">
            <span className="shrink-0 text-black dark:text-white">({romanMatch[1]})</span>
            <span><TextRenderer text={romanMatch[2]} /></span>
          </div>
        );
        i++;
        continue;
      }

      // Clause 연속 텍스트 감지: (a), (b), (c) sub-clause 뒤에 소문자로 시작하거나 (See Note...) 패턴
      // 예: "(c) adds new plumbing fixtures," 뒤에 "will result in the total daily..."
      // 예: "(b) the portion of the floor..." 뒤에 "(See Note A-11.4.3.2.(1))"
      const isContinuationText = trimmed.match(/^[a-z]/) || trimmed.match(/^\(See\s+Note/i);
      if (isContinuationText && result.length > 0) {
        // 이전 렌더링 결과 확인 (sub-clause ml-18 또는 roman ml-20)
        const lastResult = result[result.length - 1];
        const lastClassName = (lastResult as React.ReactElement)?.props?.className || '';
        if (lastClassName.includes('ml-18') || lastClassName.includes('ml-20')) {
          result.push(
            <div key={i} className="my-2 text-sm leading-relaxed text-gray-800 dark:text-gray-200 ml-18">
              <TextRenderer text={trimmed} />
            </div>
          );
          i++;
          continue;
        }
      }

      // Notes to Table 스타일링 - 헤더와 내용 전체를 하나로 묶음
      const notesToTableMatch = trimmed.match(/^Notes?\s+to\s+Table\s+([\d.]+[A-Z]?(?:-[A-Z])?):?\s*(.*)$/i);
      if (notesToTableMatch) {
        const noteContent: { type: 'table' | 'item'; content: string }[] = [];
        if (notesToTableMatch[2]) {
          noteContent.push({ type: 'item', content: notesToTableMatch[2] });
        }
        i++;

        // Note 내용 수집 (표 + - (1), - (2), ... 패턴만)
        while (i < lines.length) {
          const noteLine = lines[i].trim();
          // Note 종료 조건: 빈 줄 2개
          if (!noteLine) {
            if (i + 1 < lines.length && !lines[i + 1].trim()) {
              break;
            }
            i++;
            continue;
          }
          // 종료 조건: 대시 없이 (숫자)로 시작하면 일반 clause → Notes 종료
          if (noteLine.match(/^\(\d+\)/) && !noteLine.startsWith('-')) {
            break;
          }
          // 섹션 번호, 마크다운 헤딩, 새 테이블 제목이면 종료
          if (noteLine.match(/^\d+\.\d+\.\d+/) ||     // 섹션 번호
              noteLine.match(/^#{2,4}\s/) ||          // 마크다운 헤딩
              noteLine.match(/^<h[1-4]/) ||           // HTML 헤딩
              noteLine.match(/^(?:\*{1,2})?Table\s+\d/)) {
            break;
          }
          // <table> 태그는 Notes 안에 포함
          if (noteLine.startsWith('<table')) {
            const tableLines = [noteLine];
            if (!noteLine.includes('</table>')) {
              i++;
              while (i < lines.length) {
                tableLines.push(lines[i]);
                if (lines[i].includes('</table>')) break;
                i++;
              }
            }
            noteContent.push({ type: 'table', content: tableLines.join('\n') });
            i++;
            continue;
          }
          // - (1), - (2) 패턴만 Notes 항목으로 추가
          if (noteLine.startsWith('-') || noteLine.startsWith('•')) {
            noteContent.push({ type: 'item', content: noteLine });
          }
          i++;
        }

        result.push(
          <div key={`notes-${i}`} className="mt-4 mb-8 p-3 bg-amber-50/50 rounded-r">
            <p className="text-sm font-semibold text-amber-800 mb-2">
              Notes to Table {notesToTableMatch[1]}:
            </p>
            {noteContent.map((item, idx) => (
              item.type === 'table' ? (
                <div key={idx} className="my-2 text-xs overflow-x-auto" dangerouslySetInnerHTML={{ __html: item.content }} />
              ) : (
                <p key={idx} className="text-xs text-amber-700 mt-1 ml-2">
                  <TextRenderer text={item.content} />
                </p>
              )
            ))}
          </div>
        );
        continue;
      }

      // 수식 라인 감지 (Article 바깥)
      // "where"로 끝나는 라인은 제외
      const equationMatch = trimmed.match(/^([A-Za-z][a-z]?\s*=\s*[^,]+)$/);
      if (equationMatch && trimmed.length < 80 && /[=\+\-\/\*\(\)]/.test(trimmed) && !/\bwhere\s*$/i.test(trimmed)) {
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

          // where 블록 종료 조건
          if (!varLine ||
              varLine.match(/^\(\d+\)/) ||      // (1), (2), ...
              varLine.match(/^\([a-z]\)/) ||    // (a), (b), ...
              varLine.match(/^9\.\d+\.\d+/)) {  // 9.x.x 섹션 번호
            break;
          }

          // 변수 정의 패턴
          const varMatch = varLine.match(/^([A-Za-zγ][a-z0-9]*)\s*=\s*(.+)$/);
          if (varMatch) {
            whereContent.push(
              <span key={`var-${i}`} className="where-var">
                <span className="where-var-name">{varMatch[1]}</span> = {varMatch[2]}
              </span>
            );
            i++;
            continue;
          }

          // 연속 텍스트
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

      // HTML 테이블/제목 처리 (Part 10+ 마크다운 변환 결과)
      // 여러 줄로 분리된 테이블을 하나로 합쳐서 렌더링
      if (trimmed.startsWith('<table')) {
        const tableLines: string[] = [trimmed];
        // 첫 줄에 이미 </table>이 있으면 다음 줄 읽지 않음
        if (!trimmed.includes('</table>')) {
          i++;
          while (i < lines.length) {
            const tableLine = lines[i].trim();
            tableLines.push(tableLine);
            i++;
            if (tableLine.includes('</table>')) {
              break;
            }
          }
        } else {
          i++;
        }
        const fullTable = tableLines.join('\n');
        result.push(
          <div key={`table-${i}`} className="my-4 obc-table-container" dangerouslySetInnerHTML={{ __html: fullTable }} />
        );
        continue;
      }
      if (trimmed.startsWith('<h4') || trimmed.startsWith('<h5')) {
        // Notes to Table 특별 처리 - <h5>Notes to Table...</h5> 형식
        const notesMatch = trimmed.match(/Notes?\s+to\s+Table\s+([\d.]+[A-Z]?(?:-[A-Z])?)/i);
        if (notesMatch) {
          const noteContent: { type: 'table' | 'item'; content: string }[] = [];
          i++;

          // Note 내용 수집 (표 + - (1), - (2), ... 패턴만)
          while (i < lines.length) {
            const noteLine = lines[i].trim();
            // Note 종료 조건: 빈 줄 2개
            if (!noteLine) {
              if (i + 1 < lines.length && !lines[i + 1].trim()) {
                break;
              }
              i++;
              continue;
            }
            // 종료 조건: 대시 없이 (숫자)로 시작하면 일반 clause → Notes 종료
            if (noteLine.match(/^\(\d+\)/) && !noteLine.startsWith('-')) {
              break;
            }
            // 섹션 번호, 마크다운 헤딩, 새 테이블 제목이면 종료
            if (noteLine.match(/^\d+\.\d+\.\d+/) ||     // 섹션 번호
                noteLine.match(/^#{2,4}\s/) ||          // 마크다운 헤딩
                noteLine.match(/^<h[1-4]/) ||           // HTML 헤딩 (새 테이블 제목)
                noteLine.match(/^(?:\*{1,2})?Table\s+\d/)) {
              break;
            }
            // <table> 태그는 Notes 안에 포함
            if (noteLine.startsWith('<table')) {
              // 여러 줄 테이블 수집
              const tableLines = [noteLine];
              if (!noteLine.includes('</table>')) {
                i++;
                while (i < lines.length) {
                  tableLines.push(lines[i]);
                  if (lines[i].includes('</table>')) break;
                  i++;
                }
              }
              noteContent.push({ type: 'table', content: tableLines.join('\n') });
              i++;
              continue;
            }
            // - (1), - (2) 패턴만 Notes 항목으로 추가
            if (noteLine.startsWith('-') || noteLine.startsWith('•')) {
              noteContent.push({ type: 'item', content: noteLine });
            }
            i++;
          }

          result.push(
            <div key={`notes-${i}`} className="mt-4 mb-8 p-3 bg-amber-50/50 rounded-r">
              <p className="text-sm font-semibold text-amber-800 mb-2">
                Notes to Table {notesMatch[1]}:
              </p>
              {noteContent.map((item, idx) => (
                item.type === 'table' ? (
                  <div key={idx} className="my-2 text-xs overflow-x-auto" dangerouslySetInnerHTML={{ __html: item.content }} />
                ) : (
                  <p key={idx} className="text-xs text-amber-700 mt-1 ml-2">
                    <TextRenderer text={item.content} />
                  </p>
                )
              ))}
            </div>
          );
          continue;
        }

        // 일반 h4/h5 처리
        result.push(
          <div key={i} className="my-4" dangerouslySetInnerHTML={{ __html: trimmed }} />
        );
        i++;
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

  // 개발 모드에서만 파싱 이슈 감지
  const parsingIssues = useMemo(() => {
    if (process.env.NODE_ENV !== 'development' || !content) return [];
    const issues: string[] = [];

    // 1. 마크다운 헤딩 잔류 (### Table, ## Section 등)
    if (/^#{2,4}\s+/m.test(content)) {
      issues.push('RAW_MARKDOWN_HEADING: 마크다운 헤딩(###)이 렌더링 안됨');
    }

    // 2. 볼드/이탤릭 마크다운 잔류
    if (/^\*\*[A-Z].*\*\*$/m.test(content)) {
      issues.push('RAW_BOLD: **볼드** 마크다운이 렌더링 안됨');
    }
    if (/^\*[A-Z].*\*$/m.test(content) && !/^\*\*/.test(content)) {
      issues.push('RAW_ITALIC: *이탤릭* 마크다운이 렌더링 안됨');
    }

    // 3. Flat table 패턴 감지 (C.A. Number가 있는데 <table> 없음)
    if (/C\.A\.\s*Number.*Division B.*Compliance/i.test(content) && !/<table[\s>]/i.test(content)) {
      issues.push('FLAT_TABLE: C.A. Number 테이블이 HTML로 변환 안됨');
    }

    // 4. H.I. 테이블 패턴 감지
    if (/H\.I\.\s*\(\d+\)/.test(content) && !/Hazard Index/i.test(content) && !/<table[\s>]/i.test(content)) {
      issues.push('FLAT_HI_TABLE: H.I. 테이블이 HTML로 변환 안됨');
    }

    // 5. 테이블 헤딩이 있는데 <table> 없음
    const tableHeadingMatch = content.match(/Table\s+\d+\.\d+\.\d+\.\d*-[A-Z]/g);
    const tableTagCount = (content.match(/<table/gi) || []).length;
    if (tableHeadingMatch && tableHeadingMatch.length > tableTagCount + 2) {
      issues.push(`TABLE_MISMATCH: 테이블 헤딩 ${tableHeadingMatch.length}개, <table> ${tableTagCount}개`);
    }

    return issues;
  }, [content]);

  return (
    <HighlightProvider highlight={highlight || null}>
      <article ref={containerRef} className="max-w-[720px]">
        {/* 개발 모드 파싱 이슈 경고 */}
        {parsingIssues.length > 0 && (
          <div className="mb-4 p-3 bg-red-100 dark:bg-red-900/30 border border-red-400 dark:border-red-600 rounded-lg">
            <p className="font-bold text-red-800 dark:text-red-300 mb-2">
              ⚠️ Parsing Issues Detected ({parsingIssues.length})
            </p>
            <ul className="text-sm text-red-700 dark:text-red-400 list-disc list-inside">
              {parsingIssues.map((issue, idx) => (
                <li key={idx}>{issue}</li>
              ))}
            </ul>
          </div>
        )}

        <header className="mb-6 pb-4 border-b-2 border-gray-300 dark:border-gray-600">
          <h1 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
            <span className="font-mono text-gray-900 dark:text-gray-100 font-bold mr-2">{id}</span>
            {title}
          </h1>
        </header>

        {content ? (
          <div className="prose prose-gray dark:prose-invert max-w-none">{formattedContent}</div>
        ) : (
          <p className="text-gray-500 dark:text-gray-400">No content available for this section.</p>
        )}
      </article>
    </HighlightProvider>
  );
}
