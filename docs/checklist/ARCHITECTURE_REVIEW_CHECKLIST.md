# CodeVault 아키텍처 리뷰 리포트

> 분석일: 2026-01-17
> 대상: CodeVault (upcode-clone/codevault)
> 스택: Next.js 16.1.2 + React 19 + TypeScript + Tailwind CSS v4

---

## 요약

CodeVault 아키텍처를 종합 분석한 결과, **성능 및 코드 품질 개선**이 필요합니다:

| 카테고리 | 점수 | 상태 |
|----------|------|------|
| 구조 (Structure) | 8/10 | 깔끔한 분리, 일부 중복 |
| 디자인 패턴 (Patterns) | 8/10 | 좋은 컴포지션, 추출 필요 |
| 의존성 (Dependencies) | 7/10 | 최소 의존성, 로딩 전략 미흡 |
| 데이터 흐름 (Data Flow) | 6/10 | 작동하나 확장성 부족 |
| 성능 (Performance) | 5/10 | 번들 크기 문제 |
| 보안 (Security) | 7/10 | XSS 위험 1건 |
| **종합** | **6.8/10** | 견고한 기반, 최적화 필요 |

---

## 구현 상태 추적

### 🔴 Critical (즉시 수정)

| 항목 | 상태 | 설명 | 파일 |
|------|------|------|------|
| 테이블 HTML XSS 취약점 | ❌ | `dangerouslySetInnerHTML`에 DOMPurify 미적용 | `SectionView.tsx:186` |
| 대용량 번들 (3.2MB JSON) | ❌ | 클라이언트에 전체 JSON 로드 | `public/data/*.json` |

### 🟠 High (리팩토링)

| 항목 | 상태 | 설명 | 파일 |
|------|------|------|------|
| SectionView.tsx 과대 (623줄) | ❌ | 350줄 useMemo 파서 추출 필요 | `SectionView.tsx` |
| Error Boundary 부재 | ❌ | React 에러 경계 없음 | 앱 전체 |
| Index 기반 React Key | ⚠️ | 안정적 key 사용 필요 | `SectionView.tsx:302, 453` |
| 테이블 데이터 중복 import | ⚠️ | SectionView + CrossReferenceLink 둘 다 import | 다수 파일 |

### 🟡 Medium (코드 품질)

| 항목 | 상태 | 설명 | 파일 |
|------|------|------|------|
| Regex 패턴 분산 | ❌ | 중앙 집중화 필요 | 여러 컴포넌트 |
| JSON 유효성 검사 없음 | ❌ | Zod 스키마 추가 권장 | `lib/types.ts` |
| Loading 상태 없음 | ❌ | Suspense 경계 + 스켈레톤 | 동적 페이지 |
| 번들 분석기 없음 | ❌ | `@next/bundle-analyzer` 추가 | `package.json` |

### 🟢 Low (장기 개선)

| 항목 | 상태 | 설명 | 파일 |
|------|------|------|------|
| KaTeX 동적 로딩 | ❌ | 대부분 페이지에서 불필요 | `EquationRenderer.tsx` |
| TOC 가상화 | ❌ | react-window로 긴 목록 최적화 | `Sidebar.tsx` |
| 오프라인 지원 | ❌ | Service Worker + IndexedDB | 신규 |
| 모바일 반응형 | ❌ | 사이드바 280px 고정됨 | `Sidebar.tsx` |
| CSP 헤더 | ❌ | Content-Security-Policy 미설정 | `next.config.ts` |

---

## 발견된 이슈 상세

### 1. 보안: 테이블 HTML XSS 취약점

**위치**: `SectionView.tsx:186-187`, `CrossReferenceLink.tsx:127-128`

```tsx
// 현재 코드 (취약)
<div
  className="obc-table-container"
  dangerouslySetInnerHTML={{ __html: tableData.html }}
/>
```

**위험**: JSON 파일이 변조되면 XSS 공격 가능
**해결**: DOMPurify 적용

```tsx
// 수정 코드
import DOMPurify from 'dompurify';

<div
  className="obc-table-container"
  dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(tableData.html) }}
/>
```

---

### 2. 성능: 대용량 JSON 번들

**문제**: 3.2MB JSON이 클라이언트 번들에 포함

| 파일 | 크기 | 용도 |
|------|------|------|
| `part9.json` | 656 KB | 메인 콘텐츠 |
| `part9_tables_v9_fixed.json` | 666 KB | 테이블 (최신) |
| `part9_tables.json` | 282 KB | 테이블 (사용 중) |
| `part9-index.json` | 252 KB | 검색 인덱스 |
| `toc.json` | 32 KB | 목차 |
| 기타 레거시 | ~1.3 MB | 미사용 버전들 |

**해결 방안**:
1. 섹션별 JSON 분할 (`part9-9.1.json`, `part9-9.2.json`, ...)
2. Next.js fetch() 캐싱으로 동적 로딩
3. 레거시 파일 정리 (v8, v9 등)

---

### 3. 코드 품질: SectionView.tsx 과대

**현재**: 623줄 (Very High Complexity)

```
SectionView.tsx
├── CopyableSection (38-143) - 105줄
├── TableHTML (166-190) - 24줄
├── SectionView (192-623) - 431줄
│   └── formattedContent useMemo (238-603) - 365줄 ⚠️
```

**추출 제안**:

```
src/lib/
├── contentParser.ts        # 365줄 useMemo → 순수 함수로 추출
├── patterns.ts             # OBC regex 패턴 중앙화
└── types.ts                # 기존

src/components/code/
├── SectionView.tsx         # 200줄로 축소
├── ContentRenderer.tsx     # 파싱된 콘텐츠 렌더링
├── ArticleBlock.tsx        # Article 단위 컴포넌트
├── ClauseBlock.tsx         # (1), (a), (i) 조항 컴포넌트
└── ...
```

---

### 4. 데이터 흐름: 테이블 데이터 중복 Import

**현재**:
```
SectionView.tsx ──────┬──── tablesData (282KB)
CrossReferenceLink.tsx ┘
```

**해결**: TableDataContext 생성

```tsx
// src/contexts/TableDataContext.tsx
const TableDataContext = createContext<Record<string, TableData>>({});

export function TableDataProvider({ children }) {
  const tables = useMemo(() => tablesData, []);
  return (
    <TableDataContext.Provider value={tables}>
      {children}
    </TableDataContext.Provider>
  );
}

export const useTableData = () => useContext(TableDataContext);
```

---

## 아키텍처 품질 매트릭스

```
영향도 높음
    │
    │  ① 테이블 XSS 수정     ② JSON 분할 로딩
    │     (Critical)           (Critical)
    │
    │  ③ SectionView         ④ Error Boundary
    │     리팩토링              추가
    │     (High)               (High)
    │
    │  ⑤ Regex 중앙화        ⑥ Bundle Analyzer
    │     (Medium)              (Medium)
    │
영향도 낮음
    └──────────────────────────────────────
        구현 쉬움                구현 어려움
```

**추천 순서**: ① → ④ → ⑥ → ③ → ⑤ → ②

---

## 작업 목록

### Phase 1: Quick Wins (1-2일)

- [ ] **테이블 HTML DOMPurify 적용** (Critical)
  - 파일: `SectionView.tsx`, `CrossReferenceLink.tsx`
  - 예상: 30분

- [ ] **Error Boundary 추가** (High)
  - 파일: `src/components/ErrorBoundary.tsx` (신규)
  - 적용: `layout.tsx`에서 SectionView 감싸기
  - 예상: 1시간

- [ ] **Index 기반 Key 수정** (High)
  - 파일: `SectionView.tsx`
  - 변경: `key={i}` → `key={articleId-clause-text}`
  - 예상: 30분

- [ ] **Bundle Analyzer 추가** (Medium)
  - 설치: `npm install @next/bundle-analyzer`
  - 설정: `next.config.ts`
  - 예상: 15분

### Phase 2: 리팩토링 (3-5일)

- [ ] **contentParser.ts 추출**
  - SectionView의 365줄 useMemo를 순수 함수로 분리
  - 예상: 4시간

- [ ] **patterns.ts 생성**
  - 모든 OBC regex 패턴 중앙화
  - 예상: 2시간

- [ ] **TableDataContext 생성**
  - 테이블 데이터 Provider 패턴
  - 예상: 1시간

- [ ] **Zod 스키마 추가**
  - JSON 구조 빌드 타임 검증
  - 예상: 2시간

### Phase 3: 성능 최적화 (5-7일)

- [ ] **JSON 분할**
  - `part9.json` → 섹션별 파일 분할
  - 예상: 4시간

- [ ] **동적 JSON 로딩**
  - Next.js fetch() + 캐싱 전략
  - 예상: 6시간

- [ ] **KaTeX 동적 Import**
  - `next/dynamic`으로 lazy load
  - 예상: 1시간

- [ ] **Suspense 경계 추가**
  - 로딩 스켈레톤 UI
  - 예상: 3시간

### Phase 4: 확장 준비 (장기)

- [ ] **TOC 가상화** (react-window)
- [ ] **모바일 반응형**
- [ ] **CSP 헤더 설정**
- [ ] **오프라인 지원** (Service Worker)
- [ ] **레거시 JSON 정리**

---

## 파일별 복잡도 분석

| 파일 | 줄 수 | 복잡도 | 리팩토링 필요 |
|------|-------|--------|---------------|
| `SectionView.tsx` | 623 | Very High | ✅ 필수 |
| `CrossReferenceLink.tsx` | 267 | High | ⚠️ 권장 |
| `EquationRenderer.tsx` | 211 | Medium-High | - |
| `TextRenderer.tsx` | 152 | Medium | - |
| `Sidebar.tsx` | 133 | Medium | - |
| `DefinitionTooltip.tsx` | 128 | Medium | - |
| `Header.tsx` | 118 | Low | - |
| `search.ts` | 98 | Low | - |
| `useRecentSections.ts` | 75 | Low | - |
| `types.ts` | 44 | Very Low | - |
| `HighlightContext.tsx` | 29 | Very Low | - |

---

## 의존성 트리

```
codevault/
├── External Dependencies
│   ├── next (16.1.2) ─────────── Framework
│   ├── react (19.2.3) ────────── UI
│   ├── katex (0.16.27) ───────── Math (동적 로딩 권장)
│   ├── dompurify (3.3.1) ─────── XSS 보호 ✅
│   └── tailwindcss (4) ───────── Styling
│
├── Internal Dependencies
│   ├── lib/types.ts ──────────── 공유 타입
│   ├── lib/search.ts ─────────── 검색 알고리즘
│   ├── lib/useRecentSections.ts ─ 브라우저 상태
│   └── data/definitions.ts ───── 도메인 데이터
│
└── Data Files (3.2MB total) ⚠️
    ├── part9.json (656KB) ────── 메인 콘텐츠
    ├── part9_tables.json (282KB) ─ 테이블
    ├── part9-index.json (252KB) ── 검색 인덱스
    ├── toc.json (32KB) ───────── 목차
    └── 레거시 (2MB+) ─────────── 정리 필요
```

---

## 검증 체크리스트

### 보안 검증

- [ ] 테이블 HTML에 DOMPurify 적용 확인
- [ ] XSS 테스트: `<script>alert(1)</script>` 삽입 시도
- [ ] CSP 헤더 설정 확인

### 성능 검증

- [ ] Lighthouse 점수 측정 (목표: Performance 90+)
- [ ] Bundle Analyzer로 크기 확인 (목표: <500KB)
- [ ] LCP < 2.5s 확인
- [ ] TTI < 3.8s 확인

### 코드 품질 검증

- [ ] ESLint 경고 0개
- [ ] TypeScript strict 모드 통과
- [ ] 테스트 커버리지 (목표: 70%+)

---

## 참고 자료

### 관련 파일

- 메인 컴포넌트: `codevault/src/components/code/SectionView.tsx`
- 텍스트 렌더러: `codevault/src/components/code/TextRenderer.tsx`
- Cross-Reference: `codevault/src/components/code/CrossReferenceLink.tsx`
- 타입 정의: `codevault/src/lib/types.ts`
- 검색 알고리즘: `codevault/src/lib/search.ts`
- 데이터: `codevault/public/data/`

### 외부 문서

- [Next.js 16 App Router](https://nextjs.org/docs/app)
- [React Error Boundaries](https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary)
- [DOMPurify](https://github.com/cure53/DOMPurify)
- [@next/bundle-analyzer](https://www.npmjs.com/package/@next/bundle-analyzer)

---

## 변경 이력

| 날짜 | 내용 |
|------|------|
| 2026-01-17 | 초기 아키텍처 리뷰 작성 |
