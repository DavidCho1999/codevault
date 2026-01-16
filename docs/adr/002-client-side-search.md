# ADR-002: 클라이언트 사이드 검색

## 상태
Accepted

## 맥락

Building Code 검색 기능 구현 방식을 결정해야 했습니다.

### 요구사항
- 빠른 검색 응답 (< 100ms)
- 풀텍스트 검색 (조문 번호, 제목, 내용)
- 관련성 기반 정렬
- 검색어 하이라이팅
- 오프라인 지원 가능

### 데이터 특성
- 검색 인덱스 크기: ~500KB
- 항목 수: ~400개 서브섹션
- 텍스트 필드: id, title, content
- 업데이트 빈도: 연 1-2회

## 결정

**클라이언트 사이드에서 `useMemo`를 사용한 인메모리 검색을 구현한다.**

```typescript
// src/lib/search.ts
export function searchCode(
  index: SearchItem[],
  query: string,
  limit: number = 50
): SearchItem[] {
  const terms = query.toLowerCase().split(/\s+/).filter(Boolean);

  const scored = index.map(item => {
    let score = 0;
    for (const term of terms) {
      // ID 정확히 일치: +100
      if (item.id === term) score += 100;
      // ID 포함: +50
      else if (item.id.includes(term)) score += 50;
      // 제목 매치: +30
      if (item.title.toLowerCase().includes(term)) score += 30;
      // 내용 매치: +10
      if (item.content.toLowerCase().includes(term)) {
        score += 10;
        const matches = item.content.match(new RegExp(term, 'gi'));
        score += Math.min((matches?.length || 0) * 2, 10);
      }
    }
    return { ...item, score };
  });

  return scored
    .filter(item => item.score > 0)
    .sort((a, b) => b.score - a.score)
    .slice(0, limit);
}
```

## 선택지

### 선택지 1: 클라이언트 사이드 검색 (useMemo) ✓ 선택됨
- **장점**:
  - 즉각적인 응답 (네트워크 지연 없음)
  - 서버 비용 없음
  - 오프라인 지원 가능
  - 구현 간단
  - 작은 데이터셋에 적합
- **단점**:
  - 초기 로딩 시 인덱스 다운로드 (~500KB)
  - 복잡한 쿼리 지원 제한
  - 대규모 데이터셋에 부적합

### 선택지 2: Algolia
- **장점**:
  - 강력한 검색 기능
  - 오타 허용, 동의어 지원
  - 분석 대시보드
- **단점**:
  - 월 비용 발생 ($$$)
  - 외부 서비스 의존성
  - 설정 복잡

### 선택지 3: Elasticsearch
- **장점**:
  - 엔터프라이즈급 검색
  - 복잡한 쿼리 지원
  - 대규모 데이터 처리
- **단점**:
  - 서버 운영 필요
  - 높은 비용
  - Over-engineering

### 선택지 4: Fuse.js
- **장점**:
  - 퍼지 검색 지원
  - 클라이언트 사이드
  - 오타 허용
- **단점**:
  - 추가 의존성
  - 성능 오버헤드
  - 현재 요구사항에 과잉

### 선택지 5: Next.js API Route + SQLite
- **장점**:
  - 서버 사이드 검색
  - SQL 쿼리 유연성
  - FTS(Full Text Search) 지원
- **단점**:
  - 서버 필요
  - 응답 지연
  - 복잡한 설정

## 결과

### 긍정적
- 검색 응답 시간 < 10ms (클라이언트 측)
- 추가 서버 비용 없음
- 간단한 구현 및 유지보수
- `useMemo`로 불필요한 재계산 방지
- 오프라인 지원 가능 (Service Worker 추가 시)

### 부정적
- 초기 페이지 로드에 ~500KB 추가
- 복잡한 검색 쿼리 지원 불가 (AND, OR, 필터)
- 데이터셋이 커지면 성능 저하 가능

### 향후 마이그레이션 경로
데이터셋이 10,000개 이상으로 증가하면 Algolia 또는 Typesense로 마이그레이션 고려.

## 참고
- [React useMemo](https://react.dev/reference/react/useMemo)
- [Algolia Pricing](https://www.algolia.com/pricing/)
- [Fuse.js](https://fusejs.io/)
