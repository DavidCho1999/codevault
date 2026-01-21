# Phase 5: Next.js 연동

> 목표: SQLite 데이터베이스를 Next.js 앱에서 읽어 웹에 표시한다.

---

## 이 단계에서 배울 것

1. better-sqlite3 라이브러리 설치 및 설정
2. DB 연결 모듈 작성
3. 기존 컴포넌트를 DB 기반으로 수정
4. 정적 페이지 생성 (Static Generation)
5. 검색 기능 구현

---

## 1. better-sqlite3 설치

### 패키지 설치

```bash
cd codevault
npm install better-sqlite3
npm install -D @types/better-sqlite3
```

### 왜 better-sqlite3인가?

| 라이브러리 | 특징 | 적합성 |
|-----------|------|--------|
| better-sqlite3 | 동기식, 빠름, Node.js 전용 | Next.js SSR/SSG에 최적 |
| sql.js | WASM 기반, 브라우저 가능 | 클라이언트용 (우리는 불필요) |
| sqlite3 | 비동기, 콜백 기반 | 복잡함 |

---

## 2. DB 연결 모듈

### lib/db.ts

```typescript
// codevault/src/lib/db.ts
import Database from 'better-sqlite3';
import path from 'path';

// DB 경로 (프로젝트 루트의 obc.db)
const DB_PATH = path.join(process.cwd(), '..', 'obc.db');

// 싱글톤 패턴 - 연결 재사용
let db: Database.Database | null = null;

function getDb(): Database.Database {
    if (!db) {
        db = new Database(DB_PATH, { readonly: true });
        // 성능 최적화
        db.pragma('journal_mode = WAL');
    }
    return db;
}

// === 타입 정의 ===

export interface Node {
    id: string;
    type: 'part' | 'section' | 'subsection' | 'article' | 'sentence' | 'clause' | 'subclause';
    part: number;
    parent_id: string | null;
    title: string | null;
    content: string | null;
    page: number;
    seq: number;
}

export interface TableData {
    id: string;
    title: string | null;
    parent_id: string | null;
    page: number;
    html: string;
    source: 'manual' | 'camelot';
}

export interface Reference {
    source_id: string;
    target_id: string;
    target_type: string;
}

export interface SearchResult {
    node_id: string;
    snippet: string;
}

// === 쿼리 함수 ===

/**
 * 단일 노드 조회
 */
export function getNode(id: string): Node | undefined {
    const stmt = getDb().prepare('SELECT * FROM nodes WHERE id = ?');
    return stmt.get(id) as Node | undefined;
}

/**
 * 자식 노드 목록 조회
 */
export function getChildren(parentId: string): Node[] {
    const stmt = getDb().prepare(
        'SELECT * FROM nodes WHERE parent_id = ? ORDER BY seq'
    );
    return stmt.all(parentId) as Node[];
}

/**
 * 특정 타입의 모든 노드 조회
 */
export function getNodesByType(type: string, part: number = 9): Node[] {
    const stmt = getDb().prepare(
        'SELECT * FROM nodes WHERE type = ? AND part = ? ORDER BY seq'
    );
    return stmt.all(type, part) as Node[];
}

/**
 * 노드의 경로 (breadcrumb) 조회
 */
export function getNodePath(id: string): Node[] {
    const path: Node[] = [];
    let currentId: string | null = id;

    while (currentId) {
        const node = getNode(currentId);
        if (node) {
            path.unshift(node);
            currentId = node.parent_id;
        } else {
            break;
        }
    }

    return path;
}

/**
 * 테이블 조회
 */
export function getTable(id: string): TableData | undefined {
    const stmt = getDb().prepare('SELECT * FROM tables WHERE id = ?');
    return stmt.get(id) as TableData | undefined;
}

/**
 * 특정 노드가 참조하는 테이블 목록
 */
export function getTablesForNode(nodeId: string): TableData[] {
    const stmt = getDb().prepare(`
        SELECT t.* FROM tables t
        JOIN refs r ON t.id = r.target_id
        WHERE r.source_id = ? AND r.target_type = 'table'
    `);
    return stmt.all(nodeId) as TableData[];
}

/**
 * 노드의 참조 목록
 */
export function getReferences(sourceId: string): Reference[] {
    const stmt = getDb().prepare(
        'SELECT * FROM refs WHERE source_id = ?'
    );
    return stmt.all(sourceId) as Reference[];
}

/**
 * 전문 검색
 */
export function search(query: string, limit: number = 50): SearchResult[] {
    const stmt = getDb().prepare(`
        SELECT
            node_id,
            snippet(search_index, 2, '<mark>', '</mark>', '...', 30) as snippet
        FROM search_index
        WHERE search_index MATCH ?
        ORDER BY rank
        LIMIT ?
    `);
    return stmt.all(query, limit) as SearchResult[];
}

/**
 * Section 목록 (목차용)
 */
export function getSections(part: number = 9): Node[] {
    const stmt = getDb().prepare(`
        SELECT * FROM nodes
        WHERE part = ? AND type = 'section'
        ORDER BY seq
    `);
    return stmt.all(part) as Node[];
}

/**
 * 하위 트리 전체 조회 (성능 최적화용)
 */
export function getSubtree(parentId: string): Node[] {
    const stmt = getDb().prepare(`
        WITH RECURSIVE subtree AS (
            SELECT * FROM nodes WHERE id = ?
            UNION ALL
            SELECT n.* FROM nodes n
            JOIN subtree s ON n.parent_id = s.id
        )
        SELECT * FROM subtree ORDER BY id
    `);
    return stmt.all(parentId) as Node[];
}
```

---

## 3. 정적 페이지 생성

### generateStaticParams

Next.js 16에서는 빌드 시 모든 페이지를 미리 생성할 수 있습니다.

```typescript
// codevault/src/app/code/[...section]/page.tsx
import { getNode, getChildren, getSections, getNodesByType } from '@/lib/db';
import { SectionView } from '@/components/code/SectionView';
import { notFound } from 'next/navigation';

// 빌드 시 모든 경로 생성
export async function generateStaticParams() {
    // Section, Subsection, Article 모두 경로 생성
    const sections = getNodesByType('section');
    const subsections = getNodesByType('subsection');
    const articles = getNodesByType('article');

    const allNodes = [...sections, ...subsections, ...articles];

    return allNodes.map(node => ({
        section: node.id.split('.')
    }));
}

// 메타데이터 생성
export async function generateMetadata({ params }: { params: { section: string[] } }) {
    const id = params.section.join('.');
    const node = getNode(id);

    if (!node) {
        return { title: 'Not Found' };
    }

    return {
        title: `${node.id} - ${node.title || 'OBC Part 9'}`,
        description: node.content?.substring(0, 160) || node.title,
    };
}

// 페이지 컴포넌트
export default function Page({ params }: { params: { section: string[] } }) {
    const id = params.section.join('.');
    const node = getNode(id);

    if (!node) {
        notFound();
    }

    const children = getChildren(id);

    return (
        <SectionView
            node={node}
            children={children}
        />
    );
}
```

---

## 4. 컴포넌트 수정

### SectionView 수정

기존 JSON 기반에서 DB 기반으로 변경합니다.

```typescript
// codevault/src/components/code/SectionView.tsx
'use client';

import { Node, getChildren, getReferences, getTable } from '@/lib/db';
import { ArticleView } from './ArticleView';
import { ReferenceLink } from './ReferenceLink';

interface SectionViewProps {
    node: Node;
    children: Node[];
}

export function SectionView({ node, children }: SectionViewProps) {
    return (
        <div className="section-view">
            {/* 헤더 */}
            <header className="section-header">
                <h1 className="section-id">{node.id}</h1>
                {node.title && (
                    <h2 className="section-title">{node.title}</h2>
                )}
            </header>

            {/* 내용 */}
            {node.content && (
                <div className="section-content">
                    <ContentRenderer content={node.content} nodeId={node.id} />
                </div>
            )}

            {/* 자식 노드들 */}
            <div className="section-children">
                {children.map(child => (
                    <ChildNode key={child.id} node={child} />
                ))}
            </div>
        </div>
    );
}

function ChildNode({ node }: { node: Node }) {
    const children = getChildren(node.id);

    switch (node.type) {
        case 'subsection':
            return <SubsectionView node={node} children={children} />;
        case 'article':
            return <ArticleView node={node} children={children} />;
        case 'sentence':
            return <SentenceView node={node} children={children} />;
        default:
            return null;
    }
}
```

### ArticleView

```typescript
// codevault/src/components/code/ArticleView.tsx
import { Node } from '@/lib/db';
import { SentenceView } from './SentenceView';

interface ArticleViewProps {
    node: Node;
    children: Node[];
}

export function ArticleView({ node, children }: ArticleViewProps) {
    return (
        <article className="article-view" id={node.id}>
            <header className="article-header">
                <span className="article-id">{node.id}</span>
                {node.title && (
                    <span className="article-title">{node.title}</span>
                )}
            </header>

            <div className="article-sentences">
                {children.map(child => (
                    <SentenceView key={child.id} node={child} />
                ))}
            </div>
        </article>
    );
}
```

### SentenceView

```typescript
// codevault/src/components/code/SentenceView.tsx
import { Node, getReferences, getTable } from '@/lib/db';
import { ReferenceLink } from './ReferenceLink';
import { TableEmbed } from './TableEmbed';

interface SentenceViewProps {
    node: Node;
    children?: Node[];
}

export function SentenceView({ node, children = [] }: SentenceViewProps) {
    const refs = getReferences(node.id);
    const tableRefs = refs.filter(r => r.target_type === 'table');

    return (
        <div className="sentence-view" id={node.id}>
            {/* Sentence 번호 */}
            <span className="sentence-num">
                {extractSentenceNum(node.id)}
            </span>

            {/* 내용 (참조 링크 포함) */}
            <span className="sentence-content">
                <ContentWithLinks content={node.content || ''} refs={refs} />
            </span>

            {/* 인라인 테이블 */}
            {tableRefs.map(ref => {
                const table = getTable(ref.target_id);
                return table ? (
                    <TableEmbed key={table.id} table={table} />
                ) : null;
            })}

            {/* Clause들 */}
            {children.map(child => (
                <ClauseView key={child.id} node={child} />
            ))}
        </div>
    );
}

function extractSentenceNum(id: string): string {
    const match = id.match(/\((\d+)\)/);
    return match ? `(${match[1]})` : '';
}
```

### ReferenceLink

```typescript
// codevault/src/components/code/ReferenceLink.tsx
import Link from 'next/link';
import { Reference, getNode } from '@/lib/db';

interface ReferenceLinkProps {
    reference: Reference;
}

export function ReferenceLink({ reference }: ReferenceLinkProps) {
    const { target_id, target_type } = reference;

    // 테이블 참조
    if (target_type === 'table') {
        return (
            <a
                href={`#${target_id}`}
                className="ref-link ref-table"
                title="Jump to table"
            >
                {target_id}
            </a>
        );
    }

    // Sentence 참조 (같은 Article 내)
    if (target_type === 'sentence') {
        const targetNode = getNode(target_id);
        if (targetNode) {
            return (
                <a
                    href={`#${target_id}`}
                    className="ref-link ref-sentence"
                    title={targetNode.content?.substring(0, 100)}
                >
                    Sentence {extractSentenceNum(target_id)}
                </a>
            );
        }
    }

    // Article/Section 참조 (다른 페이지)
    if (target_type === 'article' || target_type === 'section') {
        const path = target_id.split('.').join('/');
        return (
            <Link
                href={`/code/${path}`}
                className="ref-link ref-article"
            >
                {target_id}
            </Link>
        );
    }

    return <span>{target_id}</span>;
}

function extractSentenceNum(id: string): string {
    const match = id.match(/\((\d+)\)/);
    return match ? `(${match[1]})` : id;
}
```

---

## 5. 검색 구현

### 검색 API

```typescript
// codevault/src/app/api/search/route.ts
import { NextRequest, NextResponse } from 'next/server';
import { search } from '@/lib/db';

export async function GET(request: NextRequest) {
    const query = request.nextUrl.searchParams.get('q');

    if (!query || query.length < 2) {
        return NextResponse.json({ results: [] });
    }

    try {
        const results = search(query, 50);
        return NextResponse.json({ results });
    } catch (error) {
        console.error('Search error:', error);
        return NextResponse.json(
            { error: 'Search failed' },
            { status: 500 }
        );
    }
}
```

### 검색 컴포넌트

```typescript
// codevault/src/components/search/SearchBox.tsx
'use client';

import { useState, useEffect } from 'react';
import Link from 'next/link';

interface SearchResult {
    node_id: string;
    snippet: string;
}

export function SearchBox() {
    const [query, setQuery] = useState('');
    const [results, setResults] = useState<SearchResult[]>([]);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (query.length < 2) {
            setResults([]);
            return;
        }

        const timer = setTimeout(async () => {
            setIsLoading(true);
            try {
                const res = await fetch(`/api/search?q=${encodeURIComponent(query)}`);
                const data = await res.json();
                setResults(data.results || []);
            } catch (error) {
                console.error('Search failed:', error);
            } finally {
                setIsLoading(false);
            }
        }, 300); // 디바운스

        return () => clearTimeout(timer);
    }, [query]);

    return (
        <div className="search-box">
            <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Search OBC Part 9..."
                className="search-input"
            />

            {isLoading && <div className="search-loading">Searching...</div>}

            {results.length > 0 && (
                <ul className="search-results">
                    {results.map(result => (
                        <li key={result.node_id}>
                            <Link href={`/code/${result.node_id.split('.').slice(0, 4).join('/')}`}>
                                <span className="result-id">{result.node_id}</span>
                                <span
                                    className="result-snippet"
                                    dangerouslySetInnerHTML={{ __html: result.snippet }}
                                />
                            </Link>
                        </li>
                    ))}
                </ul>
            )}
        </div>
    );
}
```

---

## 6. 목차 (Table of Contents)

### TOC 컴포넌트

```typescript
// codevault/src/components/navigation/TableOfContents.tsx
import Link from 'next/link';
import { getSections, getChildren, Node } from '@/lib/db';

export function TableOfContents() {
    const sections = getSections(9);

    return (
        <nav className="toc">
            <h2>Part 9 - Housing and Small Buildings</h2>
            <ul className="toc-list">
                {sections.map(section => (
                    <TOCSection key={section.id} section={section} />
                ))}
            </ul>
        </nav>
    );
}

function TOCSection({ section }: { section: Node }) {
    const subsections = getChildren(section.id);

    return (
        <li className="toc-section">
            <Link href={`/code/${section.id.replace(/\./g, '/')}`}>
                <span className="toc-id">{section.id}</span>
                <span className="toc-title">{section.title}</span>
            </Link>

            {subsections.length > 0 && (
                <ul className="toc-subsections">
                    {subsections.map(sub => (
                        <li key={sub.id}>
                            <Link href={`/code/${sub.id.replace(/\./g, '/')}`}>
                                <span className="toc-id">{sub.id}</span>
                                <span className="toc-title">{sub.title}</span>
                            </Link>
                        </li>
                    ))}
                </ul>
            )}
        </li>
    );
}
```

---

## 7. 실행 및 검증

### 빌드 테스트

```bash
cd codevault

# 개발 서버 실행
npm run dev

# 브라우저에서 확인
# http://localhost:3001/code/9/5/3

# 프로덕션 빌드 테스트
npm run build
```

### 검증 체크리스트

| 확인 항목 | 방법 | 예상 결과 |
|----------|------|----------|
| 섹션 페이지 로드 | /code/9/5/3 방문 | 9.5.3 내용 표시 |
| 자식 노드 표시 | 9.5.3 페이지에서 Article 확인 | 9.5.3.1, 9.5.3.2 등 표시 |
| 참조 링크 동작 | Sentence (1) 클릭 | 해당 위치로 스크롤 |
| 테이블 표시 | Table 9.5.3.1 참조 있는 페이지 | 테이블 인라인 표시 |
| 검색 동작 | "ceiling height" 검색 | 관련 결과 표시 |
| 목차 동작 | 사이드바 목차 클릭 | 해당 섹션으로 이동 |

### 콘솔 확인

```bash
# 브라우저 개발자 도구에서
# - Network 탭: API 요청 확인
# - Console: 에러 없는지 확인
```

---

## 8. 성능 최적화

### 캐싱 전략

```typescript
// next.config.js에 추가
module.exports = {
    // 정적 페이지 재검증 (ISR)
    experimental: {
        isrMemoryCacheSize: 50 * 1024 * 1024, // 50MB
    },
};
```

### DB 연결 최적화

```typescript
// lib/db.ts - 이미 싱글톤 패턴 적용됨
// WAL 모드로 읽기 성능 향상

db.pragma('journal_mode = WAL');
db.pragma('cache_size = -64000'); // 64MB 캐시
```

---

## 9. 문제 해결

### 흔한 문제들

| 문제 | 증상 | 해결 |
|------|------|------|
| DB 파일 못 찾음 | "SQLITE_CANTOPEN" 에러 | DB_PATH 확인 |
| 빌드 시 에러 | "better-sqlite3 not found" | npm rebuild |
| 페이지 404 | /code/9/5/3 접근 불가 | generateStaticParams 확인 |
| 검색 안 됨 | 결과 없음 | search_index 테이블 확인 |

### 디버깅 팁

```typescript
// 임시 디버그 로그
console.log('DB Path:', DB_PATH);
console.log('Node:', getNode('9.5.3.1'));
console.log('Children:', getChildren('9.5.3'));
```

---

## 체크리스트

- [ ] better-sqlite3 설치함
- [ ] lib/db.ts 작성함
- [ ] 타입 정의 완료
- [ ] generateStaticParams 설정함
- [ ] SectionView 컴포넌트 수정함
- [ ] 검색 API 구현함
- [ ] 검색 컴포넌트 구현함
- [ ] 목차 컴포넌트 구현함
- [ ] 개발 서버에서 테스트함
- [ ] 프로덕션 빌드 테스트함

---

## 완료 후

Phase 5 완료 시 전체 프로젝트가 완성됩니다:

1. **SQLite 기반 데이터**: 검색 가능, 관계 추적
2. **계층적 UI**: Part → Section → Article → Sentence
3. **Cross-reference**: 클릭 가능한 참조 링크
4. **전문 검색**: FTS5 기반 빠른 검색
5. **확장 준비**: Part 1-12 추가 가능

### 향후 확장

- Part 1-12 추가: `parse_part9.py`를 `parse_all.py`로 확장
- 버전 관리: `nodes` 테이블에 `version` 컬럼 추가
- 주석/북마크: 사용자 데이터 테이블 추가
