---
description: Part 9 섹션 검증 (PDF 파싱 품질 확인)
argument-hint: [섹션 ID, 예: 9.11]
model: sonnet
---

# Part 9 섹션 검증

검증 대상: **$ARGUMENTS**

---

## 필수 규칙 (반드시 준수)

> 체크리스트는 **참고용이 아니라 실행 목록**입니다.

1. **순서대로 실행**: 각 Step을 건너뛰지 않고 순서대로 실행
2. **완료 표시**: 각 Step 완료 후 체크리스트에 [x] 표시
3. **수동 확인 필수**: 자동 검증 후 반드시 사용자에게 수동 확인 요청
4. **FINAL PASS 기준**: 모든 컬럼이 [x] 또는 N/A일 때만 완료

---

## 체크리스트 파일

**경로**: `c:/Users/A/Desktop/lab/upcode-clone/_checklist/PART9_VERIFICATION_CHECKLIST.md`

---

## Step 1: 주의사항 읽기 (필수)

**체크리스트에서 읽을 섹션**: `⚠️ 검증 시 주의사항 (실수 방지)`

**실행할 것**:
1. 체크리스트 파일 열기
2. `⚠️ 검증 시 주의사항` 섹션 전체 읽기
3. 3가지 실수 패턴 확인:
   - 실수 #1: 자동 검증 OK여도 content 뒤섞임
   - 실수 #2: 수식 누락 가정하지 말고 content 먼저 검색
   - 실수 #3: where 블록 렌더링 오류
4. `필수 수동 확인 사항` 4개 항목 읽기
5. `검증 패턴 주의` 코드 확인 (올바른 패턴 vs 잘못된 패턴)

**완료 조건**: 주의사항 요약을 사용자에게 출력

---

## Step 2: 체크리스트 현황 확인

**체크리스트에서 읽을 섹션**: `Section별 검증 상태` 테이블

**실행할 것**:
1. 섹션 $ARGUMENTS 행 찾기
2. 현재 상태 출력:
   ```
   | 파싱 | Content | 수식 | 테이블 | 웹 | 비고 |
   ```
3. `Warning (확인 필요)` 섹션에서 기존 이슈 확인 (9.25 수식, 9.37 누락 등)

---

## Step 3: JSON 데이터 검증

**파일 읽기**: `c:/Users/A/Desktop/lab/upcode-clone/codevault/public/data/part9.json`

**검증 항목**:
- [ ] 섹션 존재 여부
- [ ] Content 길이 (Critical: <200자, Warning: <500자)
- [ ] Subsection 개수
- [ ] 첫 subsection content 앞 200자 출력

**출력 형식**:
```
섹션: $ARGUMENTS
Title: [제목]
Content 길이: [X]자
Subsection 수: [N]개
샘플 (첫 200자):
---
[내용]
---
```

---

## Step 4: 수동 확인 (필수!)

**체크리스트에서 읽을 섹션**: `필수 수동 확인 사항`

**4가지 항목 순서대로 실행**:
```
[ ] 자동 검증 통과 후에도 최소 3개 섹션 수동 확인
[ ] PDF 원본과 JSON content 첫 2문장 비교
[ ] Article 참조 텍스트가 뒤섞이지 않았는지 확인
    예: "Articles 9.3.1.6. and 9.3.1.7." ← 별도 블록이 되면 안됨
[ ] 수식 누락 작업 전 content에 이미 있는지 먼저 확인!
```

**이 단계 건너뛰기 금지!**

**완료 조건**: 사용자에게 "수동 확인 진행할까요?" 질문 후 승인 받기

---

## Step 5: 수식 확인 (실수 #2 방지)

**수식 섹션(9.4, 9.8, 9.25 등)인 경우**:

1. **먼저 content에서 수식 검색** (`Do =`, `S =`, `xd =` 등)
2. 이미 있으면 → N/A 또는 [x]
3. 없으면 → equations 필드 확인 or [!]

**절대 하지 말 것**: "이미지라서 누락됨" 가정하고 바로 추가

---

## Step 6: 웹 렌더링 검증 (Playwright)

**Playwright MCP 사용**:
1. `mcp__playwright__browser_navigate` → `http://localhost:3001/#$ARGUMENTS`
2. `mcp__playwright__browser_snapshot` → 페이지 구조 확인
3. `mcp__playwright__browser_take_screenshot` → 스크린샷 저장

**확인 항목**:
- [ ] 페이지 로드 성공 (에러 없음)
- [ ] 섹션 제목 표시됨
- [ ] Content 렌더링됨
- [ ] 테이블 있으면 테이블 표시됨

**스크린샷 저장**: `.playwright-mcp/verify-$ARGUMENTS.png`

---

## Step 7: PDF 원본 비교

**명령**:
```bash
python scripts_temp/extract_section_from_pdf.py $ARGUMENTS
```

**확인 항목**:
1. [ ] 섹션 제목 일치
2. [ ] 첫 subsection 시작 부분 일치
3. [ ] 참조 텍스트 뒤섞임 없음 ("Articles 9.3.1.6." 등)
4. [ ] Article 순서 정상 (9.x.x.1, 9.x.x.2, 9.x.x.3)

**결과**:
- 모두 OK → Step 8 진행
- 이슈 발견 → `CLAUDE.md` 실수 기록 확인 후 수정

---

## Step 8: 컬럼별 판정

**체크리스트에서 읽을 섹션**: `검증 패턴 주의`

| 컬럼 | 기준 | 판정 |
|------|------|------|
| 파싱 | 섹션 존재 & subsection 있음 | [x] / [ ] |
| Content | 길이 >= 200자 | [x] / [!] |
| 수식 | **content 먼저 검색** 후 판정 | [x] / [!] / N/A |
| 테이블 | tables 필드 있으면 웹에서 확인 | [x] / [!] / N/A |
| 웹 | Playwright 스크린샷 확인 | [x] / [!] |

---

## Step 9: 체크리스트 업데이트

**체크리스트 파일 수정**: `_checklist/PART9_VERIFICATION_CHECKLIST.md`

### 1. Section 테이블 업데이트
```markdown
| $ARGUMENTS | [Title] | [x] | [x] | [N/A] | [x] | [x] | [비고] |
```

### 2. 이슈 발견 시 → 피드백 테이블 추가
```markdown
| FB-XXX | $ARGUMENTS | [문제] | [해결 방법] | [날짜] |
```

### 3. 진행률 업데이트
- 완료 섹션 수 증가
- FINAL PASS면 비고에 **FINAL PASS** 표시

---

## 완료 체크

**모든 Step 완료 확인**:
```
[ ] Step 1: 주의사항 읽음
[ ] Step 2: 체크리스트 현황 확인
[ ] Step 3: JSON 검증 완료
[ ] Step 4: 수동 확인 완료 (사용자 확인 받음)
[ ] Step 5: 수식 확인 완료
[ ] Step 6: 웹 렌더링 확인 완료
[ ] Step 7: PDF 비교 완료
[ ] Step 8: 컬럼별 판정 완료
[ ] Step 9: 체크리스트 업데이트 완료
```

**FINAL PASS 조건**: 모든 Step 완료 + 모든 컬럼 [x] 또는 N/A

---

## 모델 사용 가이드

| 작업 | 모델 |
|------|------|
| 검증 (읽기/비교/확인) | **Sonnet** (기본) |
| 코드 수정 (파싱 스크립트) | **Opus** |
| 복잡한 디버깅 | **Opus** |
