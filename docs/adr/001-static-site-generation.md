# ADR-001: Static Site Generation 선택

## 상태
Accepted

## 맥락

Ontario Building Code Part 9 검색 서비스를 구축하면서 렌더링 전략을 결정해야 했습니다.

### 요구사항
- 빠른 페이지 로딩 (건축 현장에서 모바일 사용)
- SEO 최적화 (검색 엔진 인덱싱)
- 저렴한 호스팅 비용
- 콘텐츠 업데이트 빈도 낮음 (연 1-2회 OBC 개정)

### 고려 사항
- Part 9는 약 400개의 서브섹션으로 구성
- 데이터는 빌드 타임에 모두 알려져 있음
- 사용자 인증 불필요
- 실시간 데이터 업데이트 불필요

## 결정

**Next.js의 Static Site Generation (SSG)를 사용하여 모든 코드 페이지를 빌드 타임에 사전 생성한다.**

```typescript
// src/app/code/[...section]/page.tsx
export async function generateStaticParams() {
  // 모든 가능한 섹션 경로를 빌드 타임에 생성
  const params = [];
  for (const section of partData.sections) {
    params.push({ section: section.id.split('.') });
    for (const subsection of section.subsections) {
      params.push({ section: subsection.id.split('.') });
    }
  }
  return params;
}
```

## 선택지

### 선택지 1: Static Site Generation (SSG) ✓ 선택됨
- **장점**:
  - 최고의 성능 (HTML 직접 제공)
  - CDN 배포 가능 (무한 확장)
  - 낮은 호스팅 비용 (Vercel 무료 티어)
  - 높은 가용성 (서버 불필요)
  - SEO 최적화
- **단점**:
  - 빌드 시간 증가 (페이지 수에 비례)
  - 콘텐츠 업데이트 시 재빌드 필요
  - 동적 기능 제한

### 선택지 2: Server-Side Rendering (SSR)
- **장점**:
  - 실시간 데이터 반영
  - 동적 라우트 처리 용이
- **단점**:
  - 서버 비용 발생
  - 응답 시간 증가
  - 서버 유지보수 필요

### 선택지 3: Client-Side Rendering (CSR)
- **장점**:
  - 간단한 배포
  - 동적 상호작용 용이
- **단점**:
  - 초기 로딩 느림
  - SEO 문제
  - JavaScript 필수

### 선택지 4: Incremental Static Regeneration (ISR)
- **장점**:
  - SSG + 주기적 업데이트
  - 최신 데이터 반영
- **단점**:
  - 설정 복잡
  - OBC는 업데이트가 드물어 불필요

## 결과

### 긍정적
- 페이지 로딩 시간 < 100ms (CDN edge)
- Vercel 무료 티어로 운영 가능
- 검색 엔진 완전 인덱싱
- 서버 유지보수 불필요
- 높은 가용성 (99.99%)

### 부정적
- 빌드 시간 약 30초 (400+ 페이지)
- OBC 개정 시 재빌드 및 재배포 필요
- 사용자별 맞춤 기능 구현 어려움

## 참고
- [Next.js Static Generation Docs](https://nextjs.org/docs/app/building-your-application/data-fetching/fetching#static-data-fetching)
- [Vercel Edge Network](https://vercel.com/docs/edge-network/overview)
