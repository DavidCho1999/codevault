"use client";

import { useMemo } from "react";
import DOMPurify from "dompurify";
import tablesData from "../../../public/data/part9_tables.json";
import EquationRenderer from "./EquationRenderer";

interface SectionViewProps {
  id: string;
  title: string;
  content: string;
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
      <div className="my-6 p-4 border border-yellow-300 bg-yellow-50 rounded">
        <p className="text-yellow-800">Table not found: {tableId}</p>
      </div>
    );
  }

  return (
    <div className="my-6 overflow-x-auto">
      <div className="mb-3 text-center">
        <p className="font-bold text-gray-900">{tableData.title}</p>
        {subtitle && <p className="text-sm text-gray-600">{subtitle}</p>}
      </div>
      <div
        className="obc-table-container"
        dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(tableData.html) }}
      />
    </div>
  );
}

export default function SectionView({ id, title, content }: SectionViewProps) {
  const formattedContent = useMemo(() => {
    if (!content) return null;

    const lines = content.split("\n").filter((line) => line.trim());
    const result: React.ReactNode[] = [];
    let i = 0;

    while (i < lines.length) {
      const line = lines[i];
      const trimmed = line.trim();

      const tableStartMatch = trimmed.match(/^Table\s+(9\.\d+\.\d+\.\d+)(\.-[A-G])?\.\s*(.*)/);
      if (tableStartMatch) {
        const tableNum = tableStartMatch[1];
        const tableSuffix = tableStartMatch[2] || "";
        const tableId = "Table " + tableNum + tableSuffix;
        let subtitle = "";
        i++;

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
        result.push(
          <div key={i} className="mt-6 first:mt-0">
            <h3 className="text-lg font-semibold text-gray-900 mb-2">
              <span className="font-mono text-blue-600 mr-2">{articleMatch[1]}</span>
              {articleMatch[2]}
            </h3>
          </div>
        );
        i++;
        continue;
      }

      const subsectionMatch = trimmed.match(/^(\d+\.\d+\.\d+\.)\s*(.*)$/);
      if (subsectionMatch && !trimmed.includes("(")) {
        result.push(
          <div key={i} className="mt-8 first:mt-0 border-t pt-6">
            <h2 className="text-xl font-bold text-gray-900 mb-3">
              <span className="font-mono text-blue-600 mr-2">{subsectionMatch[1]}</span>
              {subsectionMatch[2]}
            </h2>
          </div>
        );
        i++;
        continue;
      }

      const clauseMatch = trimmed.match(/^\((\d+)\)\s*(.*)$/);
      if (clauseMatch) {
        result.push(
          <p key={i} className="my-3 pl-8 relative text-gray-700">
            <span className="absolute left-0 font-mono text-sm text-gray-500">({clauseMatch[1]})</span>
            <EquationRenderer text={clauseMatch[2]} />
          </p>
        );
        i++;
        continue;
      }

      const subclauseMatch = trimmed.match(/^\(([a-z])\)\s*(.*)$/);
      if (subclauseMatch) {
        result.push(
          <p key={i} className="my-2 pl-14 relative text-gray-600 text-sm">
            <span className="absolute left-8 font-mono text-gray-400">({subclauseMatch[1]})</span>
            <EquationRenderer text={subclauseMatch[2]} />
          </p>
        );
        i++;
        continue;
      }

      const romanMatch = trimmed.match(/^\((i{1,3}|iv|v|vi{0,3})\)\s*(.*)$/);
      if (romanMatch) {
        result.push(
          <p key={i} className="my-1 pl-20 relative text-gray-600 text-sm">
            <span className="absolute left-14 font-mono text-gray-400">({romanMatch[1]})</span>
            <EquationRenderer text={romanMatch[2]} />
          </p>
        );
        i++;
        continue;
      }

      if (trimmed) {
        result.push(
          <p key={i} className="my-2 text-gray-700"><EquationRenderer text={trimmed} /></p>
        );
      }
      i++;
    }

    return result;
  }, [content]);

  return (
    <article className="max-w-4xl">
      <header className="mb-6 pb-4 border-b border-gray-200">
        <h1 className="text-2xl font-bold text-gray-900">
          <span className="font-mono text-blue-600 mr-2">{id}</span>
          {title}
        </h1>
      </header>

      {content ? (
        <div className="prose prose-gray max-w-none">{formattedContent}</div>
      ) : (
        <p className="text-gray-500 italic">No content available for this section.</p>
      )}
    </article>
  );
}
