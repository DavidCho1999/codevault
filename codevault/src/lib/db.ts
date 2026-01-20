import Database from "better-sqlite3";
import path from "path";
import type { TocItem } from "./types";

// DB 경로 (프로젝트 루트의 obc.db)
const DB_PATH = path.join(process.cwd(), "..", "obc.db");

// 싱글톤 DB 인스턴스
let db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!db) {
    db = new Database(DB_PATH, { readonly: true });
  }
  return db;
}

// 타입 정의
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

// FTS5 검색
export function searchNodes(query: string, limit = 50): SearchResult[] {
  const db = getDb();

  // FTS5 검색 쿼리 (search_index 테이블 사용)
  const stmt = db.prepare(`
    SELECT
      n.id,
      n.title,
      n.content,
      n.type,
      n.parent_id,
      n.page,
      bm25(search_index) as rank
    FROM search_index s
    JOIN nodes n ON s.node_id = n.id
    WHERE search_index MATCH ?
    ORDER BY rank
    LIMIT ?
  `);

  // FTS5 쿼리 형식으로 변환 (단순 검색어 → 토큰화)
  const ftsQuery = query
    .trim()
    .split(/\s+/)
    .map((term) => `"${term}"*`)
    .join(" OR ");

  return stmt.all(ftsQuery, limit) as SearchResult[];
}

// 노드 ID로 조회
export function getNodeById(id: string): DbNode | null {
  const db = getDb();
  const stmt = db.prepare("SELECT * FROM nodes WHERE id = ?");
  return stmt.get(id) as DbNode | null;
}

// 자식 노드 조회
export function getChildNodes(parentId: string): DbNode[] {
  const db = getDb();
  const stmt = db.prepare(
    "SELECT * FROM nodes WHERE parent_id = ? ORDER BY seq"
  );
  return stmt.all(parentId) as DbNode[];
}

// 노드의 테이블 조회
export function getTablesByNodeId(nodeId: string): DbTable[] {
  const db = getDb();
  const stmt = db.prepare("SELECT * FROM tables WHERE parent_id = ?");
  return stmt.all(nodeId) as DbTable[];
}

// 특정 타입의 모든 노드 조회
export function getNodesByType(type: string): DbNode[] {
  const db = getDb();
  const stmt = db.prepare(
    "SELECT * FROM nodes WHERE type = ? ORDER BY seq"
  );
  return stmt.all(type) as DbNode[];
}

// Section과 그 하위 Subsection 조회
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
  const db = getDb();
  const stmt = db.prepare(
    "SELECT * FROM nodes WHERE type = 'section' AND id LIKE ? ORDER BY seq"
  );
  return stmt.all(`${partNum}.%`) as DbNode[];
}

// Part의 모든 content 재귀적으로 수집
export function getPartFullContent(partNum: string): { sections: DbNode[]; allContent: string } {
  const sections = getSectionsByPart(partNum);
  const contentParts: string[] = [];

  for (const section of sections) {
    // Section 헤딩
    contentParts.push(`[SECTION:${section.id}:${section.title || ""}]`);

    // Section 하위 노드들 수집
    const children = getChildNodes(section.id);
    for (const child of children) {
      if (child.type === "subsection" || child.type === "alt_subsection") {
        contentParts.push(`[SUBSECTION:${child.id}:${child.title || ""}]`);
      }

      if (child.content) {
        contentParts.push(`[ARTICLE:${child.id}:${child.title || ""}]\n${child.content}`);
      } else {
        // 손자 노드 조회
        const grandChildren = getChildNodes(child.id);
        for (const gc of grandChildren) {
          if (gc.content) {
            contentParts.push(`[ARTICLE:${gc.id}:${gc.title || ""}]\n${gc.content}`);
          }
        }
      }
    }
  }

  return { sections, allContent: contentParts.join("\n\n") };
}

// TOC 전체 조회 (사이드바용)
export function getToc(): TocItem[] {
  const db = getDb();

  // 모든 section 조회
  const sections = db
    .prepare("SELECT id, title FROM nodes WHERE type = 'section' ORDER BY seq")
    .all() as { id: string; title: string }[];

  // 각 section의 subsection 조회
  const subsectionStmt = db.prepare(
    "SELECT id, title FROM nodes WHERE parent_id = ? AND type IN ('subsection', 'alt_subsection') ORDER BY seq"
  );

  return sections.map((section) => {
    const subsections = subsectionStmt.all(section.id) as {
      id: string;
      title: string;
    }[];

    return {
      id: section.id,
      title: section.title,
      children: subsections.map((sub) => ({
        id: sub.id,
        title: sub.title,
        children: [],
      })),
    };
  });
}
