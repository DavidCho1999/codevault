# CodeVault Architecture Documentation

> Ontario Building Code Part 9 Search Service - 아키텍처 문서

---

## Overview

CodeVault는 Ontario Building Code Part 9 (Housing and Small Buildings)를 검색하고 탐색할 수 있는 웹 애플리케이션입니다.

### Quick Links

| 문서 | 설명 |
|------|------|
| [System Context](./01-system-context.md) | 시스템 전체 맥락과 외부 시스템 |
| [Container Architecture](./02-container-architecture.md) | 컨테이너 레벨 아키텍처 |
| [Component Architecture](./03-component-architecture.md) | 컴포넌트 상세 구조 |
| [Data Architecture](./04-data-architecture.md) | 데이터 흐름과 구조 |
| [Technology Stack](./05-technology-stack.md) | 기술 스택 상세 |
| [ADR Index](../adr/README.md) | 아키텍처 결정 기록 |

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        CodeVault System                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────────┐  │
│  │   PDF Source │───▶│ Python Parser│───▶│ JSON Data Files  │  │
│  │  (OBC Part 9)│    │  (PyMuPDF)   │    │ (Structured)     │  │
│  └──────────────┘    └──────────────┘    └────────┬─────────┘  │
│                                                    │            │
│                                                    ▼            │
│                      ┌─────────────────────────────────────┐   │
│                      │         Next.js 16 Application       │   │
│                      │  ┌─────────────────────────────────┐ │   │
│                      │  │      React 19 Components        │ │   │
│                      │  │  ┌────────┐ ┌────────┐ ┌──────┐│ │   │
│                      │  │  │ Header │ │Sidebar │ │Search││ │   │
│                      │  │  └────────┘ └────────┘ └──────┘│ │   │
│                      │  │  ┌────────────────────────────┐│ │   │
│                      │  │  │     SectionView + KaTeX    ││ │   │
│                      │  │  └────────────────────────────┘│ │   │
│                      │  └─────────────────────────────────┘ │   │
│                      └─────────────────────────────────────┘   │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
                                   │
                                   ▼
                         ┌─────────────────┐
                         │    Web Browser  │
                         │  (End User)     │
                         └─────────────────┘
```

---

## Key Architectural Decisions

### 1. Static Site Generation (SSG)
- 모든 코드 페이지가 빌드 타임에 사전 생성됨
- 빠른 페이지 로딩과 SEO 최적화

### 2. Client-Side Search
- `useMemo` 기반 클라이언트 검색
- API 호출 없이 즉각적인 검색 결과

### 3. JSON Data Layer
- PDF 데이터를 JSON으로 사전 변환
- 계층적 구조로 효율적인 탐색

### 4. Math Rendering with KaTeX
- 수학 공식을 LaTeX로 변환
- 빠른 렌더링 성능

---

## Project Statistics

| Metric | Value |
|--------|-------|
| Framework | Next.js 16.1.2 |
| React Version | 19.2.3 |
| TypeScript | 5.x |
| Source Files | 10 files |
| Components | 5 components |
| Lines of Code | ~900 lines |

---

## Documentation Standards

이 문서는 다음 표준을 따릅니다:

- **C4 Model**: Context, Container, Component, Code 레벨 다이어그램
- **ADR (Architecture Decision Records)**: 주요 결정 기록
- **Mermaid**: 다이어그램 as code

---

*Generated: 2026-01-16*
*Version: 1.0.0*
