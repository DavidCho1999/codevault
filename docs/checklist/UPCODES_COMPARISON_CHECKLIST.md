# CodeVault vs UpCodes 비교 분석 리포트

> 분석일: 2026-01-16 (최종 업데이트: 2026-01-17)
> 비교 대상: UpCodes (Illinois IBC 2024 뷰어)
> 참고 파일: `reference/upcode_contents1.html`

---

## 요약

UpCodes 레퍼런스와 CodeVault를 비교한 결과, **UX 및 기능적 격차**가 발견되었습니다:

1. ~~**Cross-Reference 링크 부재**~~ ✅ 완료
2. ~~**Definition 연결 없음**~~ ✅ 완료
3. **테이블 셀 병합 문제** - rowspan/colspan 미적용 (일부 해결)
4. **섹션 인터랙션 부족** - Floating Action Buttons 미구현
5. ~~**텍스트 서식 손실**~~ ✅ Notes 스타일링 완료

---

## 구현 상태 추적

### 🔴 Critical (핵심 기능)

| 항목 | 상태 | 진행 내용 |
|------|------|----------|
| Cross-Reference 자동 링크 | ✅ | ~~미구현~~ → Article, Table, Sentence 등 582개 참조 링크 완료 |
| Definition 용어 연결 | ✅ | ~~미구현~~ → 30개 주요 정의어 호버 툴팁 완료 |
| 테이블 셀 병합 | ⚠️ | Table 9.3.2.1 수동 수정 완료 (rowspan/colspan 적용) |

### 🟠 High (UX 개선)

| 항목 | 상태 | 진행 내용 |
|------|------|----------|
| 섹션 Hover 효과 | ✅ | ~~기본 hover만~~ → 호버 시 링크 복사 버튼 표시 |
| 섹션별 Permalink | ✅ | ~~미구현~~ → URL hash 지원 (`#9.10.9.1`) + 자동 스크롤 |
| 링크/텍스트 복사 버튼 | ✅ | ~~미구현~~ → 클릭 시 클립보드 복사 + 체크 아이콘 피드백 |
| 검색 결과 하이라이트 | ✅ | ~~미구현~~ → 검색 결과 클릭 시 페이지 내 검색어 노란색 하이라이트 |
| 이탤릭체/볼드 서식 | ⚠️ | 일부만 적용 (`<i>loadbearing</i>` 등) |
| Notes/Exceptions 스타일링 | ✅ | ~~미구현~~ → 테이블 노트 박스 + (See Note) 인라인 스타일링 |

### 🟡 Medium (기능 개선)

| 항목 | 상태 | 진행 내용 |
|------|------|----------|
| 계층 구조 들여쓰기 | ✅ | ~~테두리 선~~ → flex 레이아웃 + ml-8/ml-16 들여쓰기 |
| 테이블 제목/Notes 표시 | ✅ | ~~Table 9.3.1.7 Notes 누락~~ → 추가됨 (노란 배경 + 주황 테두리 박스) |
| 중복 제목 제거 | ✅ | 섹션 content에서 현재 섹션 ID와 일치하는 제목 스킵 |

### 🟢 Low (추가 기능 - 장기)

| 항목 | 상태 | 진행 내용 |
|------|------|----------|
| 다크 모드 | ✅ | ~~미구현~~ → 클래스 기반 다크 모드 완료 (Tailwind v4) |
| 인쇄 기능 | ✅ | ~~미구현~~ → Print CSS 완료 (헤더/사이드바 숨김, 전체 너비 출력) |
| 북마크 시스템 | ❌ | 미구현 (사용자 계정 필요) |
| 댓글/메모 | ❌ | 미구현 |
| AI Copilot | ❌ | 미구현 |
| 코드 버전 비교 | ❌ | 미구현 |

---

## Floating Action Buttons (UpCodes 참조)

UpCodes는 각 섹션 호버 시 **7개의 액션 버튼**이 우측 상단에 표시됩니다:

| 버튼 | aria-label | 기능 | CodeVault 상태 |
|------|------------|------|----------------|
| 📋 Copy code section | "Copy code section" | 섹션 텍스트 복사 | ✅ 구현됨 |
| 🔗 Copy link | "Copy link" | 링크 복사 | ✅ 구현됨 |
| 🔀 Code compare | "Code compare" | 버전 비교 | ❌ 미구현 |
| 🖨️ Print this section | "Print this section" | 섹션만 인쇄 | ✅ 구현됨 |
| 💬 Add comment | "Add comment" | 메모 추가 | ❌ 미구현 |
| 🔖 Bookmark | "Bookmark" | 북마크 | ❌ 미구현 |
| 🤖 Ask Copilot | "Ask Copilot" | AI 질문 | ❌ 미구현 |

### Section Backdrop 효과

| 기능 | UpCodes | CodeVault |
|------|---------|-----------|
| 호버 시 배경색 | 연한 회색 (`group-hover:bg-gray-100`) | ✅ 구현됨 (`hover:bg-gray-50`) |
| 선택 시 배경색 | 파란색 (`bg-blue-50 border-blue-300`) | ❌ 없음 |
| 들여쓰기 레벨 | `ind-0` ~ `ind-5` 클래스 | ✅ ml-8, ml-16으로 구현 |

---

## 추가 기능 (신규 발견)

### 🟠 High Priority

| 항목 | 상태 | 설명 |
|------|------|------|
| 섹션 텍스트 복사 버튼 | ✅ | 섹션 내용 클립보드 복사 |
| 섹션 호버 배경 효과 | ✅ | 호버 시 연회색 배경 (`hover:bg-gray-50`) |
| 모바일 반응형 | ❌ | 현재 데스크톱 전용 (사이드바 280px 고정) |

### 🟡 Medium Priority

| 항목 | 상태 | 설명 |
|------|------|------|
| 섹션별 인쇄 | ✅ | 특정 섹션만 인쇄 (새 창에서 인쇄) |
| 키보드 네비게이션 | ✅ | ↑/↓ 키로 페이지 스크롤 (150px씩) |
| 최근 본 섹션 | ✅ | localStorage + 실시간 동기화 (사이드바 상단) |
| Related Sections | ❌ | 관련 섹션 추천 카드 |

### 🟢 Low Priority

| 항목 | 상태 | 설명 |
|------|------|------|
| User Notes / About Chapter | ❌ | 챕터 소개 박스 (UpCodes 스타일) |
| QR 코드 | ❌ | 섹션별 QR 코드 생성 |
| 클릭 선택 하이라이트 | ✅ | 섹션 클릭 시 파란색 배경 + 왼쪽 테두리 |

---

## 테이블 셀 병합 상세 진행

| 테이블 | 상태 | 비고 |
|--------|------|------|
| Table 9.3.2.1 | ✅ | rowspan/colspan 수동 적용 완료 |
| Table 9.4.3.1 | ❌ | 미수정 |
| Table 9.6.1.3.-A~G | ❌ | 미수정 - 복잡한 헤더 구조 |
| Table 9.8.4.1 | ❌ | 미수정 |
| Table 9.15.4.2 | ❌ | 미수정 |
| Table 9.23.3.5 | ❌ | 미수정 |
| 기타 테이블 | ❌ | 검토 필요 |

---

## 상세 분석

### Cross-Reference 패턴

OBC Part 9에서 발견되는 참조 패턴:

| 패턴 | 예시 | 빈도 | 구현 |
|------|------|------|------|
| Section X.X.X.X | "See Section 9.23.4.1" | 높음 | ❌ |
| Article X.X.X.X | "Article 9.15.4.5" | 높음 | ❌ |
| Sentence X.X.X.X.(X) | "Sentence 9.10.9.4.(2)" | 중간 | ❌ |
| Table X.X.X.X | "Table 9.3.2.1" | 높음 | ❌ |
| Subsection X.X.X | "Subsection 9.23" | 낮음 | ❌ |

### Definition 용어 목록 (구현됨 ✅)

| 용어 | 정의 존재 | 자동 링크 |
|------|-----------|----------|
| loadbearing | ✅ | ✅ |
| fire separation | ✅ | ✅ |
| dwelling unit | ✅ | ✅ |
| building height | ✅ | ✅ |
| storey | ✅ | ✅ |
| secondary suite | ✅ | ✅ |
| 기타 24개 용어 | ✅ | ✅ |

---

## 구현 우선순위

**추천 순서**: ① → ③ → ② → ④

```
영향도 높음
    │
    │  ① Cross-Reference    ② Definition 연결
    │     자동 링크
    │
    │  ③ 테이블 병합        ④ 섹션 액션 버튼
    │
    │  ⑤ 검색 하이라이트    ⑥ 이탤릭체 복원
    │
영향도 낮음
    └──────────────────────────────────────
        구현 쉬움                구현 어려움
```

---

## 다음 단계

### 완료된 항목
- [x] Cross-Reference 자동 링크 구현
- [x] 9.2 Definitions 용어 목록 추출
- [x] Definition 자동 링크 구현
- [x] 섹션별 Permalink + 링크 복사 버튼
- [x] 검색 하이라이트
- [x] 다크 모드
- [x] 인쇄 기능

### 진행 중
- [ ] 주요 테이블 병합 수정 (9.4.3.1, 9.6.1.3, 9.8.4.1 등)

### 다음 우선순위
1. [x] 섹션 텍스트 복사 버튼 (쉬움) ✅ 2026-01-17
2. [x] 섹션 호버 배경 효과 (쉬움) ✅ 2026-01-17
3. [ ] 모바일 반응형 (중요)
4. [x] 섹션별 인쇄 (중간) ✅ 2026-01-17
5. [x] 키보드 네비게이션 (중간) ✅ 2026-01-17
6. [x] 최근 본 섹션 히스토리 (중간) ✅ 2026-01-17

---

## 검증 로그

### 2026-01-16 테이블 셀 병합 테스트

**Table 9.3.2.1 수정:**
- 상태: ✅ **완료**
- 적용: `rowspan="4"` (Use), `colspan="3"` (Boards), `rowspan="3"` (All Species)
- 파일: `codevault/public/data/part9_tables.json`
- 결과: PDF 원본과 동일한 헤더 구조로 표시됨

### 2026-01-16 Definition 용어 툴팁 테스트

**Definition 용어 연결:**
- 상태: ✅ **완료**
- 구현: 30개 OBC 주요 정의어 하드코딩 (`definitions.ts`)
- 컴포넌트: `DefinitionTooltip.tsx` (호버 툴팁)
- 스타일: 파란색 이탤릭체 + 호버 시 점선 밑줄
- 테스트: Section 9.10.9에서 "fire separation", "secondary suite" 확인

**포함된 정의어 (30개):**
loadbearing, fire separation, dwelling unit, storey, occupancy, fire-resistance rating, combustible, noncombustible, firewall, fire compartment, building height, grade, means of egress, exit, suite, secondary suite, habitable room, service room, vapour barrier, air barrier, thermal resistance, crawl space, attic, basement, joist, rafter, stud, sheathing, cladding, flashing

**TODO: 정의어 확장 필요**
- 현재: 30개 (수동 선정)
- OBC 전체: **351개** (Division A, Section 1.4.1.2에서 확인)
- 커버리지: 8.5%
- 출처: `source/2024 Building Code Compendium/301880.pdf` 페이지 81~150

### 2026-01-17 Permalink + 복사 버튼 테스트

**섹션별 Permalink:**
- 상태: ✅ **완료**
- URL 형식: `/code/9.10.9#9.10.9.1`
- 자동 스크롤: hash 위치로 smooth scroll + 노란색 하이라이트 (2초)
- 파일: `SectionView.tsx`

**링크 복사 버튼:**
- 상태: ✅ **완료**
- 트리거: Article/Subsection 호버 시 왼쪽에 링크 아이콘 표시
- 동작: 클릭 시 클립보드 복사 + 체크 아이콘 피드백 (2초)
- 컴포넌트: `CopyableSection` (SectionView.tsx 내부)

### 2026-01-17 검색 하이라이트 테스트

**검색 결과 하이라이트:**
- 상태: ✅ **완료**
- URL 형식: `/code/9/9/4?highlight=fire`
- 구현: React Context (`HighlightContext`) + RegExp 매칭
- 스타일: `<mark>` 태그 + 노란색 배경 (`bg-yellow-200`)
- 파일: `TextRenderer.tsx`, `HighlightContext.tsx`, `page.tsx`
- 테스트: "fire" 검색 → 결과 클릭 → 페이지 내 모든 "fire" 노란색 하이라이트

### 2026-01-17 계층 구조 시각적 구분선 테스트

**계층 구조 시각화:**
- 상태: ✅ **완료** (이후 수정됨)
- 초기 구현: 왼쪽 테두리 선(border-left)으로 조항 레벨 구분
- **업데이트**: 사용자 피드백으로 테두리 선 제거 → flex 레이아웃으로 변경
- 현재 스타일:
  - (1), (2) 숫자 조항: `flex gap-2` + 들여쓰기 없음
  - (a), (b) 알파벳 하위조항: `flex gap-2 ml-8`
  - (i), (ii) 로마숫자 하위조항: `flex gap-2 ml-16`
- 파일: `SectionView.tsx`

### 2026-01-17 중복 제목 수정

**섹션 제목 중복 제거:**
- 상태: ✅ **완료**
- 문제: 각 섹션에서 제목이 두 번 표시됨 (header + content 내부)
- 해결: content 파싱 시 현재 섹션 ID와 일치하는 제목 라인 스킵
- 파일: `SectionView.tsx`
- 코드: `if (lineId === id) { i++; continue; }`

### 2026-01-17 Floating Action Buttons 구현

**섹션 호버 시 액션 버튼 그룹:**
- 상태: ✅ **완료**
- 구현 버튼:
  - 📋 텍스트 복사 (`handleCopyText`) - 섹션 innerText 클립보드 복사
  - 🔗 링크 복사 (`handleCopyLink`) - Permalink URL 복사
  - 🖨️ 섹션 인쇄 (`handlePrintSection`) - 새 창에서 해당 섹션만 인쇄
- 위치: 섹션 우측 상단 (UpCodes 스타일)
- 스타일: 흰색 배경 + 테두리 + 그림자, 호버 시 표시
- 파일: `SectionView.tsx` (`CopyableSection` 컴포넌트)

**섹션 호버 배경 효과:**
- 상태: ✅ **완료**
- 스타일: `hover:bg-gray-50 dark:hover:bg-gray-800/50`
- 적용: Article, Subsection 레벨

### 2026-01-17 Notes/Exceptions 스타일링 테스트

**Notes to Table 스타일링:**
- 상태: ✅ **완료**
- 스타일: 노란색 배경 (`#fffbeb`) + 주황색 왼쪽 테두리 (4px)
- 적용: CSS (`.obc-table-container > div:last-child`)
- 테스트: Section 9.3.1의 Table 9.3.1.7. 하단 노트 확인

**인라인 Note 참조 스타일링:**
- 상태: ✅ **완료**
- 패턴: `(See Note A-X.X.X.X.)`, `(See Notes A-X.X.X.X. and A-X.X.X.X.)`
- 스타일: 주황색 이탤릭체 (`text-amber-600 text-sm italic`)
- 파일: `TextRenderer.tsx` (`parseNotes` 함수)
- 테스트: Section 9.8.4의 "(See Note A-9.8.4.)" 확인

### 2026-01-17 다크 모드 구현

**다크 모드:**
- 상태: ✅ **완료**
- 구현: Tailwind v4 `@custom-variant dark` + localStorage 저장
- 토글: Header.tsx 우측 상단 Sun/Moon 아이콘
- 적용 범위:
  - Header: 배경, 테두리, 텍스트, 검색창
  - Sidebar: 배경, 테두리, 메뉴 항목
  - SectionView: 제목, 본문, 조항 테두리, 테이블
  - 스크롤바: 다크 테마 적용
- 파일: `globals.css`, `Header.tsx`, `Sidebar.tsx`, `SectionView.tsx`, `layout.tsx`

### 2026-01-17 인쇄 기능 구현

**인쇄 스타일:**
- 상태: ✅ **완료**
- 구현: `@media print` CSS
- 숨김 요소: header, nav, aside, sidebar, button
- 본문: 전체 너비 (100%), 흰 배경, 검정 텍스트
- 링크: URL 표시 (`content: " (" attr(href) ")"`)
- 테이블: `page-break-inside: avoid`
- 사용법: 브라우저 `Ctrl+P` 또는 `인쇄` 메뉴

---

## 참고 자료

- UpCodes 레퍼런스: `reference/upcode_contents1.html`
- 현재 컴포넌트: `codevault/src/components/code/SectionView.tsx`
- 테이블 데이터: `codevault/public/data/part9_tables.json`
- Cross-Reference: `codevault/src/components/code/CrossReferenceLink.tsx`
- Definition 툴팁: `codevault/src/components/code/DefinitionTooltip.tsx`
- 정의어 목록: `codevault/src/data/definitions.ts`
- 텍스트 렌더러: `codevault/src/components/code/TextRenderer.tsx`
- 하이라이트 컨텍스트: `codevault/src/components/code/HighlightContext.tsx`
- 최근 섹션 훅: `codevault/src/lib/useRecentSections.ts`

---

## 추가 검증 로그

### 2026-01-17 키보드 네비게이션 구현

**↑/↓ 키 페이지 스크롤:**
- 상태: ✅ **완료**
- 구현: `useEffect` + `keydown` 이벤트 리스너
- 동작:
  - ArrowDown: 아래로 150px 스크롤
  - ArrowUp: 위로 150px 스크롤
  - smooth behavior 적용
- 예외: input, textarea 요소 포커스 시 무시
- 파일: `SectionView.tsx`

### 2026-01-17 최근 본 섹션 기능 구현

**Recent Sections 히스토리:**
- 상태: ✅ **완료**
- 구현:
  - `useRecentSections` 훅 생성 (localStorage 기반)
  - 최대 8개 섹션 저장 (표시는 5개)
  - 실시간 동기화: `recent-sections-updated` 커스텀 이벤트
- 저장 형식: `{ id, title, visitedAt }`
- localStorage 키: `codevault-recent-sections`
- UI 위치: 사이드바 상단 (Recent 라벨 + 시계 아이콘)
- 파일: `useRecentSections.ts`, `Sidebar.tsx`, `SectionView.tsx`
- 테스트: 섹션 방문 → 사이드바에 즉시 반영 (새로고침 불필요)

### 2026-01-17 클릭 선택 하이라이트 구현

**섹션 클릭 시 파란색 하이라이트:**
- 상태: ✅ **완료**
- 구현:
  - `selectedSection` 상태 + `handleSelectSection` 핸들러
  - `CopyableSection`에 `isSelected`, `onSelect` props 추가
- 스타일: `bg-blue-50 border-l-4 border-blue-400` (다크 모드 지원)
- 동작:
  - 섹션 클릭 → 파란색 하이라이트 적용
  - 다른 섹션 클릭 → 선택 변경
  - 같은 섹션 클릭 → 토글 해제
- 파일: `SectionView.tsx`
- E2E 테스트: Playwright로 에러 없음 확인
