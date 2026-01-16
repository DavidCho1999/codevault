# ADR-003: JSON 데이터 레이어

## 상태
Accepted

## 맥락

PDF에서 추출한 Building Code 데이터를 저장하고 애플리케이션에서 사용할 방식을 결정해야 했습니다.

### 요구사항
- 빠른 데이터 접근
- 정적 사이트 생성과 호환
- 간단한 데이터 구조
- 버전 관리 가능
- 빌드 타임에 데이터 사용

### 데이터 특성
- 계층 구조 (Part → Section → Subsection → Article)
- 텍스트 중심 (조문 내용)
- 읽기 전용 (런타임에 수정 없음)
- 총 용량 ~3MB

## 결정

**정적 JSON 파일을 `public/data/` 폴더에 저장하고 Static Import로 사용한다.**

```
public/data/
├── part9.json          # 전체 콘텐츠 (~2MB)
├── part9-index.json    # 검색 인덱스 (~500KB)
├── toc.json            # 네비게이션 트리 (~50KB)
└── part9_tables.json   # HTML 테이블 (~100KB)
```

```typescript
// 사용 예시 - Static Import
import partData from '@/public/data/part9.json';
import tocData from '@/public/data/toc.json';

// 빌드 타임에 JSON이 번들에 포함됨
```

## 선택지

### 선택지 1: Static JSON Files ✓ 선택됨
- **장점**:
  - 데이터베이스 불필요
  - Git으로 버전 관리
  - 빌드 타임에 최적화
  - 구현 간단
  - CDN 캐싱
- **단점**:
  - 동적 업데이트 불가
  - 대용량 데이터에 부적합
  - 관계형 쿼리 불가

### 선택지 2: SQLite + Prisma
- **장점**:
  - SQL 쿼리 지원
  - 관계형 데이터 모델링
  - 대용량 데이터 처리
- **단점**:
  - 서버 필요 (API Route)
  - 설정 복잡
  - Over-engineering

### 선택지 3: Markdown/MDX Files
- **장점**:
  - 콘텐츠 편집 용이
  - Git-friendly
  - 내장 컴포넌트
- **단점**:
  - 구조화된 데이터에 부적합
  - 검색 인덱싱 어려움
  - 파일 수 많아짐

### 선택지 4: CMS (Contentful, Sanity)
- **장점**:
  - 관리 UI 제공
  - 미디어 관리
  - 협업 기능
- **단점**:
  - 월 비용 발생
  - 외부 의존성
  - API 호출 필요

### 선택지 5: Firebase Firestore
- **장점**:
  - 실시간 동기화
  - 확장성
  - SDK 제공
- **단점**:
  - 비용 발생
  - 오프라인 지원 복잡
  - SSG와 통합 어려움

## 결과

### 긍정적
- 빌드 타임에 모든 데이터 접근
- 추가 인프라 비용 없음
- Git으로 데이터 변경 추적
- 빠른 페이지 로딩 (번들에 포함)
- 간단한 데이터 파이프라인

### 부정적
- 데이터 업데이트 시 재빌드 필요
- 대규모 데이터에 번들 크기 증가
- 런타임 데이터 수정 불가

### 데이터 파이프라인

```
PDF Source
    ↓ (Manual: python parse_obc_v2.py)
JSON Files
    ↓ (npm run build)
Next.js Bundle
    ↓ (Deploy)
Production Site
```

## 참고
- [Next.js Static File Serving](https://nextjs.org/docs/app/building-your-application/optimizing/static-assets)
- [JSON Import in Next.js](https://nextjs.org/docs/app/building-your-application/configuring/typescript#statically-typed-links)
