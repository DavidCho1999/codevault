# Architecture Decision Records (ADR)

> CodeVault 프로젝트의 주요 아키텍처 결정 기록

---

## ADR이란?

Architecture Decision Records(ADR)는 프로젝트에서 내린 중요한 아키텍처 결정을 문서화합니다.
각 ADR은 결정의 맥락, 선택지, 결정 이유, 그리고 결과를 포함합니다.

---

## ADR 목록

| ID | 제목 | 상태 | 날짜 |
|----|------|------|------|
| [ADR-001](./001-static-site-generation.md) | Static Site Generation 선택 | Accepted | 2026-01-16 |
| [ADR-002](./002-client-side-search.md) | 클라이언트 사이드 검색 | Accepted | 2026-01-16 |
| [ADR-003](./003-json-data-layer.md) | JSON 데이터 레이어 | Accepted | 2026-01-16 |
| [ADR-004](./004-katex-math-rendering.md) | KaTeX 수식 렌더링 | Accepted | 2026-01-16 |
| [ADR-005](./005-tailwind-css-v4.md) | Tailwind CSS v4 선택 | Accepted | 2026-01-16 |

---

## 상태 정의

| 상태 | 의미 |
|------|------|
| **Proposed** | 제안됨, 검토 필요 |
| **Accepted** | 승인됨, 구현됨 |
| **Deprecated** | 더 이상 권장하지 않음 |
| **Superseded** | 다른 ADR로 대체됨 |

---

## ADR 템플릿

새로운 ADR 작성 시 다음 템플릿을 사용하세요:

```markdown
# ADR-XXX: [제목]

## 상태
[Proposed | Accepted | Deprecated | Superseded]

## 맥락
[결정이 필요한 배경과 문제 설명]

## 결정
[선택한 해결 방안]

## 선택지
### 선택지 1: [이름]
- 장점: ...
- 단점: ...

### 선택지 2: [이름]
- 장점: ...
- 단점: ...

## 결과
### 긍정적
- ...

### 부정적
- ...

## 참고
- [관련 링크]
```

---

*[아키텍처 문서로 돌아가기](../architecture/README.md)*
