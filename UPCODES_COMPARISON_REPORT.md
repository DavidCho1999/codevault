# CodeVault vs UpCodes 비교 분석 리포트

> 분석일: 2026-01-16
> 비교 대상: UpCodes (Illinois IBC 2024 뷰어)
> 참고 파일: `reference/upcode_contents1.html`

---

## 요약

UpCodes 레퍼런스와 CodeVault를 비교한 결과, **UX 및 기능적 격차**가 발견되었습니다:

1. **Cross-Reference 링크 부재** - 섹션 간 참조가 클릭 불가능
2. **Definition 연결 없음** - 용어 정의로 이동 불가
3. **테이블 셀 병합 문제** - rowspan/colspan 미적용 (일부 해결)
4. **섹션 인터랙션 부족** - 액션 버튼, 호버 효과 미흡
5. **텍스트 서식 손실** - 이탤릭체, Notes 스타일링 누락

---

## 구현 상태 추적

### 🔴 Critical (핵심 기능)

| 항목 | 상태 | 진행 내용 |
|------|------|----------|
| Cross-Reference 자동 링크 | ✅ | ~~미구현~~ → Article, Table, Sentence 등 582개 참조 링크 완료 |
| Definition 용어 연결 | ❌ | 미구현 - `loadbearing` 등 정의어 링크 없음 |
| 테이블 셀 병합 | ⚠️ | Table 9.3.2.1 수동 수정 완료 (rowspan/colspan 적용) |

### 🟠 High (UX 개선)

| 항목 | 상태 | 진행 내용 |
|------|------|----------|
| 섹션 Hover 효과 | ⚠️ | 기본 hover만 존재, 액션 버튼 없음 |
| 섹션별 Permalink | ❌ | 미구현 - 특정 조항 URL 공유 불가 |
| 링크/텍스트 복사 버튼 | ❌ | 미구현 |
| 검색 결과 하이라이트 | ❌ | 미구현 - 검색어 강조 없음 |
| 이탤릭체/볼드 서식 | ⚠️ | 일부만 적용 (`<i>loadbearing</i>` 등) |
| Notes/Exceptions 스타일링 | ❌ | 미구현 - 일반 텍스트로 표시 |

### 🟡 Medium (기능 개선)

| 항목 | 상태 | 진행 내용 |
|------|------|----------|
| 계층 구조 들여쓰기 | ⚠️ | 기본적인 들여쓰기만 적용 |
| 테이블 제목/Notes 표시 | ⚠️ | ~~Table 9.3.1.7 Notes 누락~~ → 추가됨 |

### 🟢 Low (추가 기능 - 장기)

| 항목 | 상태 | 진행 내용 |
|------|------|----------|
| 북마크 시스템 | ❌ | 미구현 (사용자 계정 필요) |
| 인쇄 기능 | ❌ | 미구현 (브라우저 기본 인쇄로 대체 가능) |
| 댓글/메모 | ❌ | 미구현 |
| AI Copilot | ❌ | 미구현 |
| 코드 버전 비교 | ❌ | 미구현 |
| 다크 모드 | ❌ | 미구현 |

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

### Definition 용어 목록 (예시)

| 용어 | 9.2 정의 존재 | 자동 링크 |
|------|--------------|----------|
| loadbearing | ✅ | ❌ |
| fire separation | ✅ | ❌ |
| dwelling unit | ✅ | ❌ |
| building height | ✅ | ❌ |
| storey | ✅ | ❌ |

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

- [ ] Cross-Reference 자동 링크 구현
- [ ] 주요 테이블 병합 수정 (9.4.3.1, 9.6.1.3, 9.8.4.1 등)
- [ ] 9.2 Definitions 용어 목록 추출
- [ ] Definition 자동 링크 구현
- [ ] 섹션 복사/링크 복사 버튼 추가

---

## 검증 로그

### 2026-01-16 테이블 셀 병합 테스트

**Table 9.3.2.1 수정:**
- 상태: ✅ **완료**
- 적용: `rowspan="4"` (Use), `colspan="3"` (Boards), `rowspan="3"` (All Species)
- 파일: `codevault/public/data/part9_tables.json`
- 결과: PDF 원본과 동일한 헤더 구조로 표시됨

---

## 참고 자료

- UpCodes 레퍼런스: `reference/upcode_contents1.html`
- 현재 컴포넌트: `codevault/src/components/code/SectionView.tsx`
- 테이블 데이터: `codevault/public/data/part9_tables.json`
