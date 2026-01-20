-- ============================================================
-- OBC Part 9 Example Data
-- ============================================================
-- 참고: _checklist/structure/phase1_schema.md
-- 용도: 스키마 테스트 및 쿼리 검증
-- ============================================================
-- 사용법:
--   sqlite3 obc.db < scripts/schema.sql
--   sqlite3 obc.db < scripts/examples.sql
-- ============================================================

-- ============================================================
-- 1. Part (최상위)
-- ============================================================

INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
VALUES ('9', 'part', 9, NULL, 'Housing and Small Buildings', NULL, 711, 1);

-- ============================================================
-- 2. Sections
-- ============================================================

INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq) VALUES
('9.4', 'section', 9, '9', 'Structural Requirements', NULL, 718, 4),
('9.5', 'section', 9, '9', 'Design of Areas, Spaces and Doorways', NULL, 750, 5),
('9.6', 'section', 9, '9', 'Doors and Windows', NULL, 760, 6);

-- ============================================================
-- 3. Subsections (일반)
-- ============================================================

INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq) VALUES
-- 9.5의 자식들
('9.5.1', 'subsection', 9, '9.5', 'General', NULL, 750, 1),
('9.5.2', 'subsection', 9, '9.5', 'Barrier-Free Design', NULL, 751, 2),
('9.5.3', 'subsection', 9, '9.5', 'Ceiling Heights', NULL, 752, 3);

-- ============================================================
-- 4. Alternative Subsections (9.5.3의 형제!)
-- ============================================================
-- 주의: parent_id = '9.5' (9.5.3이 아님!)

INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq) VALUES
('9.5.3A', 'alt_subsection', 9, '9.5', 'Living Rooms or Spaces Within Dwelling Units', NULL, 753, 4),
('9.5.3B', 'alt_subsection', 9, '9.5', 'Dining Rooms or Spaces Within Dwelling Units', NULL, 753, 5),
('9.5.3C', 'alt_subsection', 9, '9.5', 'Kitchens Within Dwelling Units', NULL, 754, 6),
('9.5.3D', 'alt_subsection', 9, '9.5', 'Bedrooms Within Dwelling Units', NULL, 754, 7),
('9.5.3E', 'alt_subsection', 9, '9.5', 'Combined Spaces Within Dwelling Units', NULL, 755, 8),
('9.5.3F', 'alt_subsection', 9, '9.5', 'Bathrooms Within Dwelling Units', NULL, 755, 9),
('9.5.4', 'subsection', 9, '9.5', 'Doorways and Doors', NULL, 756, 10);

-- ============================================================
-- 5. Articles (일반)
-- ============================================================

INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq) VALUES
-- 9.5.1의 자식들
('9.5.1.1', 'article', 9, '9.5.1', 'Method of Measurement', NULL, 750, 2),
('9.5.1.2', 'article', 9, '9.5.1', 'Minimum Areas', NULL, 750, 4),

-- 9.5.3의 자식들
('9.5.3.1', 'article', 9, '9.5.3', 'Ceiling Heights of Rooms or Spaces', NULL, 752, 1),
('9.5.3.2', 'article', 9, '9.5.3', 'Sloped Ceilings', NULL, 752, 2);

-- ============================================================
-- 6. 특수 Articles
-- ============================================================

-- 0A Article (9.5.1.1보다 먼저!)
INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
VALUES ('9.5.1.0A', 'article_0a', 9, '9.5.1', 'Application', NULL, 750, 1);

-- Article + Suffix (9.5.1.1 바로 뒤)
INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq)
VALUES ('9.5.1.1A', 'article_suffix', 9, '9.5.1', 'Floor Areas', NULL, 750, 3);

-- Sub-Article (Alternative Subsection의 자식)
INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq) VALUES
('9.5.3A.1', 'sub_article', 9, '9.5.3A', 'Areas of Living Rooms', NULL, 753, 1),
('9.5.3D.1', 'sub_article', 9, '9.5.3D', 'Areas of Bedrooms', NULL, 754, 1),
('9.5.3D.2', 'sub_article', 9, '9.5.3D', 'Dimensions of Bedrooms', NULL, 754, 2);

-- ============================================================
-- 7. Clauses (실제 텍스트 내용)
-- ============================================================

-- 9.5.3.1의 Clause들
INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq) VALUES
('9.5.3.1.(1)', 'clause', 9, '9.5.3.1', NULL,
 'Except as provided in Sentence (2), the minimum height of ceilings in rooms or spaces shall conform to Table 9.5.3.1.',
 752, 1),
('9.5.3.1.(2)', 'clause', 9, '9.5.3.1', NULL,
 'Ceiling heights shall be reduced by the thickness of any flooring to be installed over the structural floor.',
 752, 2);

-- 9.5.1.1의 Clause들
INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq) VALUES
('9.5.1.1.(1)', 'clause', 9, '9.5.1.1', NULL,
 'Except as provided in Sentences (2) and (3), areas shall be measured as the area enclosed by the finished surfaces of the walls.',
 750, 1),
('9.5.1.1.(2)', 'clause', 9, '9.5.1.1', NULL,
 'Where a room has a sloped ceiling, only that part of the room where the ceiling height is 2.1 m or more shall be included in the calculation of floor area.',
 750, 2);

-- ============================================================
-- 8. Sub-clauses
-- ============================================================

INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq) VALUES
('9.5.3.1.(1)(a)', 'subclause', 9, '9.5.3.1.(1)', NULL,
 'where one or more habitable rooms have a floor area less than 10 m²',
 752, 1),
('9.5.3.1.(1)(b)', 'subclause', 9, '9.5.3.1.(1)', NULL,
 'where all habitable rooms have a floor area of 10 m² or more',
 752, 2);

-- ============================================================
-- 9. Sub-sub-clauses
-- ============================================================

INSERT INTO nodes (id, type, part, parent_id, title, content, page, seq) VALUES
('9.5.3.1.(1)(a)(i)', 'subsubclause', 9, '9.5.3.1.(1)(a)', NULL,
 'the width of the room shall be measured perpendicular to the entrance',
 752, 1),
('9.5.3.1.(1)(a)(ii)', 'subsubclause', 9, '9.5.3.1.(1)(a)', NULL,
 'the depth of the room shall be measured parallel to the entrance',
 752, 2);

-- ============================================================
-- 10. Tables
-- ============================================================

INSERT INTO tables (id, title, parent_id, page, html, source) VALUES
('Table 9.5.3.1', 'Room Ceiling Heights', '9.5.3.1', 752, NULL, 'pending'),
('Table 9.5.3.2', 'Sloped Ceiling Requirements', '9.5.3.2', 752, NULL, 'pending');

-- ============================================================
-- 11. Cross-references
-- ============================================================

-- 9.5.3.1.(1)이 Table 9.5.3.1을 참조
INSERT INTO refs (source_id, target_id, target_type)
VALUES ('9.5.3.1.(1)', 'Table 9.5.3.1', 'table');

-- 9.5.3.1.(1)이 Sentence (2)를 참조
INSERT INTO refs (source_id, target_id, target_type)
VALUES ('9.5.3.1.(1)', '9.5.3.1.(2)', 'clause');

-- 9.5.1.1.(1)이 Sentence (2)를 참조
INSERT INTO refs (source_id, target_id, target_type)
VALUES ('9.5.1.1.(1)', '9.5.1.1.(2)', 'clause');

-- ============================================================
-- 검증 쿼리
-- ============================================================
-- 아래 쿼리들로 데이터 확인:
--
-- 1. 전체 노드 수:
--    SELECT type, COUNT(*) FROM nodes GROUP BY type;
--
-- 2. 9.5의 직접 자식들 (seq 순서):
--    SELECT id, type, seq FROM nodes WHERE parent_id = '9.5' ORDER BY seq;
--
-- 3. Alternative Subsection 확인:
--    SELECT id, title FROM nodes WHERE type = 'alt_subsection';
--
-- 4. 특수 Article 확인:
--    SELECT id, type, title FROM nodes WHERE type IN ('article_0a', 'article_suffix', 'sub_article');
--
-- 5. Clause 계층 (9.5.3.1):
--    SELECT id, type, content FROM nodes WHERE parent_id LIKE '9.5.3.1%' ORDER BY id;
--
-- 6. 테이블-Article 연결:
--    SELECT t.id, t.title, n.title as article_title
--    FROM tables t JOIN nodes n ON t.parent_id = n.id;
--
-- 7. Cross-reference:
--    SELECT * FROM refs;
--
-- 8. 전문 검색 테스트:
--    SELECT node_id, title FROM search_index WHERE search_index MATCH 'ceiling';
-- ============================================================
