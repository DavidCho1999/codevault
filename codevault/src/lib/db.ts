// JSON 기반 데이터 로더 (Vercel 호환)
import type { TocItem } from "./types";

// JSON 데이터 import
import part2Data from "../../public/data/part2.json";
import part6Data from "../../public/data/part6.json";
import part7Data from "../../public/data/part7.json";
import part8Data from "../../public/data/part8.json";
import part9Data from "../../public/data/part9.json";
import part10Data from "../../public/data/part10.json";
import part11Data from "../../public/data/part11.json";
import part12Data from "../../public/data/part12.json";

// 타입 정의 (page는 optional - Part 2 등에 없음)
interface JsonSubsection {
  id: string;
  title: string;
  page?: number;
  content?: string;
  articles?: { id: string; title: string; content: string }[];
}

interface JsonSection {
  id: string;
  title: string;
  page?: number;
  subsections: JsonSubsection[];
}

interface JsonPart {
  id: string;
  title: string;
  division?: string;
  sections: JsonSection[];
}

// 모든 Part 데이터
const allParts: JsonPart[] = [
  part2Data as JsonPart,
  part6Data as JsonPart,
  part7Data as JsonPart,
  part8Data as JsonPart,
  part9Data as JsonPart,
  part10Data as JsonPart,
  part11Data as JsonPart,
  part12Data as JsonPart,
];

// DB 호환 타입
export interface DbNode {
  id: string;
  type: "part" | "section" | "subsection" | "alt_subsection" | "article" | "article_suffix" | "article_0a" | "sub_article" | "clause";
  parent_id: string | null;
  title: string;
  page: number;
  content: string | null;
  seq: number;
}

export interface DbTable {
  id: string;
  title: string | null;
  parent_id: string | null;
  page: number | null;
  html: string;
  source: string | null;
}

export interface SearchResult {
  id: string;
  title: string;
  content: string;
  type: string;
  parent_id: string | null;
  page: number;
  rank: number;
}

// 헬퍼: Part 번호 추출
function getPartNum(id: string): string {
  return id.split(".")[0];
}

// 헬퍼: Part 데이터 찾기
function findPart(partNum: string): JsonPart | undefined {
  return allParts.find((p) => p.id === partNum);
}

// 노드 ID로 조회
export function getNodeById(id: string): DbNode | null {
  const partNum = getPartNum(id);
  const part = findPart(partNum);
  if (!part) return null;

  // Part 자체
  if (id === partNum) {
    return {
      id: part.id,
      type: "part",
      parent_id: null,
      title: part.title,
      page: part.sections[0]?.page || 0,
      content: null,
      seq: parseInt(partNum),
    };
  }

  // Section 찾기
  for (const section of part.sections) {
    if (section.id === id) {
      return {
        id: section.id,
        type: "section",
        parent_id: partNum,
        title: section.title,
        page: section.page || 0,
        content: null,
        seq: parseFloat(section.id) * 100,
      };
    }

    // Subsection 찾기
    for (const sub of section.subsections) {
      if (sub.id === id) {
        const isAlt = /[A-Z]$/.test(sub.id);
        return {
          id: sub.id,
          type: isAlt ? "alt_subsection" : "subsection",
          parent_id: section.id,
          title: sub.title,
          page: sub.page || 0,
          content: sub.content || null,
          seq: parseFloat(sub.id.replace(/[A-Z]$/, "")) * 1000,
        };
      }
    }
  }

  return null;
}

// 자식 노드 조회
export function getChildNodes(parentId: string): DbNode[] {
  const partNum = getPartNum(parentId);
  const part = findPart(partNum);
  if (!part) return [];

  if (parentId === partNum) {
    return part.sections.map((section, idx) => ({
      id: section.id,
      type: "section" as const,
      parent_id: partNum,
      title: section.title,
      page: section.page || 0,
      content: null,
      seq: idx,
    }));
  }

  for (const section of part.sections) {
    if (section.id === parentId) {
      return section.subsections.map((sub, idx) => {
        const isAlt = /[A-Z]$/.test(sub.id);
        return {
          id: sub.id,
          type: isAlt ? "alt_subsection" : "subsection",
          parent_id: section.id,
          title: sub.title,
          page: sub.page || 0,
          content: sub.content || null,
          seq: idx,
        } as DbNode;
      });
    }
  }

  return [];
}

// 테이블 조회
export function getTablesByNodeId(nodeId: string): DbTable[] {
  return [];
}

// 특정 타입의 모든 노드 조회
export function getNodesByType(type: string): DbNode[] {
  const results: DbNode[] = [];

  for (const part of allParts) {
    if (type === "part") {
      results.push({
        id: part.id,
        type: "part",
        parent_id: null,
        title: part.title,
        page: part.sections[0]?.page || 0,
        content: null,
        seq: parseInt(part.id),
      });
    } else if (type === "section") {
      for (const section of part.sections) {
        results.push({
          id: section.id,
          type: "section",
          parent_id: part.id,
          title: section.title,
          page: section.page || 0,
          content: null,
          seq: parseFloat(section.id) * 100,
        });
      }
    } else if (type === "subsection" || type === "alt_subsection") {
      for (const section of part.sections) {
        for (const sub of section.subsections) {
          const isAlt = /[A-Z]$/.test(sub.id);
          if ((type === "alt_subsection" && isAlt) || (type === "subsection" && !isAlt)) {
            results.push({
              id: sub.id,
              type: isAlt ? "alt_subsection" : "subsection",
              parent_id: section.id,
              title: sub.title,
              page: sub.page || 0,
              content: sub.content || null,
              seq: parseFloat(sub.id.replace(/[A-Z]$/, "")) * 1000,
            });
          }
        }
      }
    }
  }

  return results.sort((a, b) => a.seq - b.seq);
}

// Section과 하위 Subsection 조회
export function getSectionWithSubsections(sectionId: string): {
  section: DbNode;
  subsections: DbNode[];
} | null {
  const section = getNodeById(sectionId);
  if (!section || section.type !== "section") return null;

  const subsections = getChildNodes(sectionId);
  return { section, subsections };
}

// Part 번호로 해당 Part의 모든 Section 조회
export function getSectionsByPart(partNum: string): DbNode[] {
  const part = findPart(partNum);
  if (!part) return [];

  return part.sections.map((section, idx) => ({
    id: section.id,
    type: "section" as const,
    parent_id: partNum,
    title: section.title,
    page: section.page || 0,
    content: null,
    seq: idx,
  }));
}

// Part의 모든 content 재귀적으로 수집
export function getPartFullContent(partNum: string): { sections: DbNode[]; allContent: string } {
  const part = findPart(partNum);
  if (!part) return { sections: [], allContent: "" };

  const sections = getSectionsByPart(partNum);
  const contentParts: string[] = [];

  for (const section of part.sections) {
    contentParts.push("[SECTION:" + section.id + ":" + (section.title || "") + "]");

    for (const sub of section.subsections) {
      contentParts.push("[SUBSECTION:" + sub.id + ":" + (sub.title || "") + "]");

      if (sub.content) {
        contentParts.push(sub.content);
      }
    }
  }

  return { sections, allContent: contentParts.join("\n\n") };
}

// 검색 (클라이언트 검색)
export function searchNodes(query: string, limit = 50): SearchResult[] {
  const results: SearchResult[] = [];
  const lowerQuery = query.toLowerCase();
  const queryTerms = lowerQuery.split(/\s+/).filter(Boolean);

  for (const part of allParts) {
    for (const section of part.sections) {
      for (const sub of section.subsections) {
        const content = sub.content || "";
        const title = sub.title || "";
        const searchText = (title + " " + content).toLowerCase();

        const matches = queryTerms.every((term) => searchText.includes(term));

        if (matches) {
          let rank = 0;
          if (title.toLowerCase().includes(lowerQuery)) {
            rank = -10;
          }

          results.push({
            id: sub.id,
            title: sub.title,
            content: content.slice(0, 500),
            type: "subsection",
            parent_id: section.id,
            page: sub.page || 0,
            rank,
          });
        }
      }
    }
  }

  return results.sort((a, b) => a.rank - b.rank).slice(0, limit);
}

// TOC 전체 조회 (사이드바용)
export function getToc(): TocItem[] {
  const tocItems: TocItem[] = [];

  for (const part of allParts) {
    for (const section of part.sections) {
      tocItems.push({
        id: section.id,
        title: section.title,
        children: section.subsections.map((sub) => ({
          id: sub.id,
          title: sub.title,
          children: [],
        })),
      });
    }
  }

  return tocItems;
}

// 하위 호환성
export function getDb(): null {
  return null;
}
