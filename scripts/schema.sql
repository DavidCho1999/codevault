-- ============================================================
-- OBC Part 9 Database Schema
-- ============================================================
-- 참고: _checklist/structure/phase1_schema.md
-- 생성일: 2026-01-18
-- ============================================================

PRAGMA foreign_keys = ON;

-- ============================================================
-- 1. nodes 테이블 (핵심 - 계층 구조)
-- ============================================================
-- type 가능 값:
--   'part'           : 9
--   'section'        : 9.X
--   'subsection'     : 9.X.X
--   'alt_subsection' : 9.X.X[A-Z]  (Alternative Subsection)
--   'article'        : 9.X.X.X
--   'article_suffix' : 9.X.X.X[A-Z]  (예: 9.5.1.1A, 9.33.6.10A)
--   'article_0a'     : 9.X.X.0A      (예: 9.5.1.0A)
--   'sub_article'    : 9.X.X[A-Z].X
--   'clause'         : (1), (2)...
--   'subclause'      : (a), (b)...
--   'subsubclause'   : (i), (ii)...

CREATE TABLE IF NOT EXISTS nodes (
    id TEXT PRIMARY KEY,            -- "9.5.3.1" 또는 "9.5.3A" 또는 "9.5.3.1.(1)"
    type TEXT NOT NULL,             -- 위 타입 목록 참조
    part INTEGER NOT NULL,          -- 9 (Part 번호)

    parent_id TEXT,                 -- 부모 노드 ID

    title TEXT,                     -- "Ceiling Heights" (Article 이상만)
    content TEXT,                   -- 실제 텍스트 (Clause 이하만)

    page INTEGER,                   -- PDF 페이지 번호
    seq INTEGER,                    -- 형제 노드 중 순서 (1, 2, 3...)

    FOREIGN KEY (parent_id) REFERENCES nodes(id)
);

-- ============================================================
-- 2. tables 테이블 (OBC 테이블)
-- ============================================================
-- source 가능 값:
--   'pending'  : 아직 추출 안 됨
--   'camelot'  : Camelot으로 자동 추출
--   'manual'   : 수동 입력/수정

CREATE TABLE IF NOT EXISTS tables (
    id TEXT PRIMARY KEY,            -- "Table 9.5.3.1"
    title TEXT,                     -- "Room Ceiling Heights"
    parent_id TEXT,                 -- "9.5.3.1" - 참조하는 Article ID
    page INTEGER,                   -- PDF 페이지 번호
    html TEXT,                      -- 렌더링용 HTML
    source TEXT DEFAULT 'pending',  -- "pending" | "camelot" | "manual"

    FOREIGN KEY (parent_id) REFERENCES nodes(id)
);

-- ============================================================
-- 3. refs 테이블 (Cross-reference)
-- ============================================================
-- target_type 가능 값:
--   'clause'  : 다른 Clause 참조 (예: "Sentence (2)")
--   'article' : 다른 Article 참조 (예: "Article 9.5.3.2")
--   'table'   : 테이블 참조 (예: "Table 9.5.3.1")
--   'section' : 섹션 참조 (예: "Section 9.5")

CREATE TABLE IF NOT EXISTS refs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL,        -- "9.5.3.1.(1)" - 참조하는 노드
    target_id TEXT NOT NULL,        -- "9.5.3.2" or "Table 9.5.3.1"
    target_type TEXT,               -- "clause", "table", "article", "section"

    FOREIGN KEY (source_id) REFERENCES nodes(id)
);

-- ============================================================
-- 4. search_index (FTS5 전문 검색)
-- ============================================================

CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
    node_id,
    title,
    content,
    tokenize='porter unicode61'
);

-- ============================================================
-- 5. 동기화 트리거 (nodes 변경 시 search_index 자동 업데이트)
-- ============================================================

-- INSERT 트리거
CREATE TRIGGER IF NOT EXISTS nodes_ai AFTER INSERT ON nodes BEGIN
    INSERT INTO search_index(node_id, title, content)
    VALUES (new.id, new.title, new.content);
END;

-- UPDATE 트리거
CREATE TRIGGER IF NOT EXISTS nodes_au AFTER UPDATE ON nodes BEGIN
    UPDATE search_index
    SET title = new.title, content = new.content
    WHERE node_id = new.id;
END;

-- DELETE 트리거
CREATE TRIGGER IF NOT EXISTS nodes_ad AFTER DELETE ON nodes BEGIN
    DELETE FROM search_index WHERE node_id = old.id;
END;

-- ============================================================
-- 6. 인덱스
-- ============================================================

CREATE INDEX IF NOT EXISTS idx_nodes_parent ON nodes(parent_id);
CREATE INDEX IF NOT EXISTS idx_nodes_type ON nodes(type);
CREATE INDEX IF NOT EXISTS idx_nodes_part ON nodes(part);
CREATE INDEX IF NOT EXISTS idx_nodes_seq ON nodes(parent_id, seq);

CREATE INDEX IF NOT EXISTS idx_tables_parent ON tables(parent_id);

CREATE INDEX IF NOT EXISTS idx_refs_source ON refs(source_id);
CREATE INDEX IF NOT EXISTS idx_refs_target ON refs(target_id);

-- ============================================================
-- 완료
-- ============================================================
-- 사용법:
--   sqlite3 obc.db < schema.sql
--
-- 테스트:
--   sqlite3 obc.db ".tables"
--   sqlite3 obc.db ".schema nodes"
-- ============================================================
