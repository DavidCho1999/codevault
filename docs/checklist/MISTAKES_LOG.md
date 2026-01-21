# 실수 기록 (Mistakes Log)

> PDF 파싱 및 검증 작업 중 발생한 실수와 해결 방법
>
> 마지막 업데이트: 2026-01-18

---

## 빠른 참조

| # | 카테고리 | 요약 | 해결 |
|---|----------|------|------|
| 1 | PDF 파싱 | 텍스트 순서 뒤섞임 | y좌표 → x좌표 정렬 |
| 2 | PDF 파싱 | 섹션 경계 분리 실패 | 섹션 ID 패턴 사용 |
| 3 | 환경 | npm run dev 종료 | 기존 프로세스 확인 |
| 4 | PDF 파싱 | 섹션 내용 잘림 | Article 레벨 파싱 |
| 5 | 검증 | 참조 텍스트를 Article로 오인 | `\n...+[A-Z]` 패턴 |
| 6 | PDF 파싱 | 수식 이미지 추출 불가 | 수동 입력 |
| 7 | PDF 파싱 | end_pattern 불일치 | `(?:\n\|\s{2,})` 패턴 |
| 8 | 렌더링 | clause 줄바꿈 누락 | SectionView 전처리 |
| 9 | 테이블 | MERGE 구조 미확인 | PDF 이미지 비교 필수 |
| 10 | 테이블 | HTML 태그 이스케이프 | 유니코드 사용 |
| 14 | 렌더링 | 수식/변수 줄바꿈 합쳐짐 | `[a-zγ]{1,3}\s*=` 패턴 추가 |
| 15 | 렌더링 | where 블록 조기 종료 | 종료 조건 구체화 |

---

## 상세 기록

### #1: PDF 텍스트 순서 뒤섞임 (2026-01-15)

**문제**: `page.get_text()`로 추출 시 순서 뒤섞임
**증상**: 9.1.1.7이 9.1.1.1보다 위에 표시
**원인**: PDF 내부 블록 순서 ≠ 시각적 순서
**해결**: `page.get_text("blocks")` + y좌표 → x좌표 정렬

---

### #2: 섹션 경계 분리 실패 (2026-01-15)

**문제**: 여러 페이지 텍스트 단순 연결로 섹션 혼합
**증상**: 9.2 Definitions 비어있고 내용이 9.3에 포함
**원인**: `for p in range(page, next_page)` 단순 연결
**해결**: 섹션 ID 패턴(예: 9.2.1.)으로 경계 분리

---

### #3: npm run dev 실행 시 Claude Code 종료 (2026-01-17)

**문제**: 서버 실행 시 Claude Code 종료
**원인**: 기존 Next.js 프로세스 + lock 파일 충돌
**해결**:
```bash
netstat -ano | findstr :3001
taskkill /PID <PID> /F
# 또는 .next/dev/lock 삭제
```

---

### #4: 섹션 내용 잘림 - Critical (2026-01-17)

**문제**: Subsection 내 Article 누락
**증상**: 9.4.2 - Article 2, 3 전체 누락, 578자 (원본 20%)
**원인**: `extract_subsection_content()`가 상위 Subsection ID만 인식
**해결**:
1. Article 레벨까지 파싱 확장
2. 같은 레벨 다음 Article까지 파싱
3. 모든 섹션 content 길이 검증 필수

---

### #5: 참조 텍스트를 Article로 오인 - Critical (2026-01-17)

**문제**: 자동 검증 "OK"지만 content 뒤섞임
**증상**: "Articles 9.3.1.6. and 9.3.1.7."에서 9.3.1.6을 Article로 오인
**원인**: 패턴 `\b(9\.\d+\.\d+\.\d+)\.?\s`가 참조도 매칭
**해결**:
```python
# 잘못된 패턴
r'\b(9\.\d+\.\d+\.\d+)\.?\s'

# 올바른 패턴 (줄 시작 + 대문자)
r'\n(9\.\d+\.\d+\.\d+)\.\s+[A-Z]'
```

---

### #6: PDF 수식 이미지 추출 불가 - Critical (2026-01-17)

**문제**: 수식이 이미지로 저장되어 텍스트 추출 불가
**증상**: 9.4.2.2 (5) `xd = 5(h - 0.55Ss/γ)` 누락
**영향**: 9.4.2, 9.25, 9.8 등 수식 섹션
**해결**: 주요 수식 수동 입력
```json
"9.4.2.2.(5)": "xd = 5(h - 0.55Ss/γ)"
```

---

### #7: end_pattern 불일치 - Critical (2026-01-17)

**문제**: 패턴이 실제 PDF 형식과 불일치
**증상**: 9.7.1에 9.7.2 내용 포함 (1087자 → 435자)
**원인**: 패턴이 줄바꿈 기대, 실제는 공백 4개
**해결**:
```python
# 변경 전
end_pattern = "\n" + re.escape(next_sub_id) + r"\.\s*\n"

# 변경 후
end_pattern = r"(?:\n|\s{2,})" + re.escape(next_sub_id) + r"\.\s+"
```

---

### #8: clause 줄바꿈 누락 (2026-01-18)

**문제**: (a), (b) clause가 한 줄로 연결, 문장 끝 분리
**증상**: 9.8.6.3.(4) "...shall be (a) where... (b) where..."
**해결**: SectionView.tsx 전처리 추가
```typescript
processedContent = processedContent.replace(/\n(?![(\d9A-Z])/g, ' ');
```

---

### #9: 테이블 MERGE 구조 미확인 - Critical (2026-01-18)

**문제**: caption만 추가하고 병합 구조 미확인
**증상**: Table 9.4.3.1 첫 열이 빈 셀로 처리
**원인**: Camelot 자동 변환이 복잡한 병합 인식 못함
**해결**:
1. PDF 이미지 추출: `extract_table_image.py`
2. rowspan/colspan 개수 확인
3. 불일치 시 완전한 data + spans 오버라이드

**핵심**: "렌더링됨" ≠ "병합 구조 정확"

---

### #10: HTML 태그 이스케이프 (2026-01-18)

**문제**: `<sup>` 태그가 텍스트로 표시
**원인**: JSON → HTML 변환 시 `<` `>` 이스케이프
**해결**: 유니코드 사용
```
위첨자: ⁽¹⁾ ⁽²⁾ ⁽³⁾
아래첨자: ₁ ₂ ₃
```

---

### #11: Tailwind 클래스 미적용 (2026-01-18)

**문제**: `class="text-center"` 동적 HTML에서 작동 안 함
**원인**: dangerouslySetInnerHTML 렌더링 시 Tailwind 미인식
**해결**: inline style 사용
```html
<th style="text-align: center;">
```

---

### #12: 팝업 헤더-caption 중복 (2026-01-18)

**문제**: "Table 9.3.1.7" 두 번 표시
**해결**: caption_html에서 "Table X.X.X." 제거

---

### #13: Caption에 "Forming Part of..." 포함하여 중복 표시 (2026-01-18)

**문제**: "Forming Part of Sentence X.X.X.X.(N)"가 두 번 표시됨
```
1. 팝업 헤더 아래에 subtitle로 표시
2. caption 내부에 <br/>Forming Part of...로 표시
→ 중복 발생
```

**증상**: Table 9.7.3.3에서 발견
- 팝업 헤더 아래: "Forming Part of Sentence 9.7.3.3.(3)"
- caption 제목 아래: "Forming Part of Sentence 9.7.3.3.(3)"

**원인**: caption_html에 `<br/>Forming Part of...` 포함

**해결**:
```html
<!-- ❌ 잘못됨 -->
<caption>
  <strong>제목</strong><br/>
  Forming Part of Sentence X.X.X.X.(N)
</caption>

<!-- ✅ 올바름 -->
<caption>
  <strong>제목</strong>
</caption>
```

**관련 파일**:
- `.claude/commands/table.md` (라인 25)
- `_checklist/TABLE_QUALITY_GUIDE.md` (라인 13, 68-77, 159)
- `manual_table_overrides.json` (9.7.2.3, 9.7.3.3 수정 완료)

---

### #14: 수식/변수 줄바꿈 합쳐짐 (2026-01-18)

**문제**: 소문자 수식, where, 그리스 문자 변수가 이전 줄과 합쳐짐
**증상**:
- `S = CbSs + Sr where` (수식+where 합쳐짐)
- `...as follows: xd = 5(h...)` (xd 수식 인라인)
- `h = height..., and γ = specific...` (h와 γ 합쳐짐)

**원인**: SectionView.tsx:265 전처리가 소문자/그리스 문자 시작 줄 합침
```typescript
// 변경 전
processedContent = processedContent.replace(/\n(?![(\d9A-Z])/g, ' ');
```

**해결** (최종):
```typescript
// 변경 후: where, 소문자 수식(xd=), 그리스 문자(γ=) 유지
processedContent = processedContent.replace(/\n(?!where\b|[a-zγ]{1,3}\s*=|[(\d9A-Z])/g, ' ');
```
- `where\b` - where 키워드
- `[a-zγ]{1,3}\s*=` - xd=, h=, γ= 같은 변수 정의

---

### #15: where 블록 조기 종료 (2026-01-18)

**문제**: where 블록 내용 중 숫자로 시작하는 줄에서 종료
**증상**: 9.4.2.2.(1) where 블록에서 "0.55 for all other roofs"가 밖으로 나감
**원인**: 종료 조건 `/^[\(\d]/`가 너무 광범위
```typescript
// 변경 전: 숫자나 괄호 시작 모두 종료
if (varLine.match(/^[\(\d]/) || varLine.match(/^\d+\.\d+/)) {
  break;
}
```
**해결**:
```typescript
// 변경 후: clause/섹션 번호만 종료
if (varLine.match(/^\(\d+\)/) ||      // (1), (2)
    varLine.match(/^\([a-z]\)/) ||    // (a), (b)
    varLine.match(/^9\.\d+\.\d+/)) {  // 9.x.x
  break;
}
```
**수정 위치**: SectionView.tsx 471-474번, 634-637번 줄 (2곳)

---

## 예방 체크리스트

```
[ ] 자동 검증 후 최소 3개 섹션 수동 확인
[ ] PDF 원본과 JSON content 첫 2문장 비교
[ ] 수식 작업 전 content에 이미 있는지 확인
[ ] 테이블 작업 시 PDF 이미지 먼저 추출
[ ] 병합 구조 (rowspan/colspan) PDF와 비교
[ ] 수식 렌더링 시 "where" 블록이 별도로 표시되는지 확인
[ ] where 블록 검증 시 모든 변수 정의가 블록 안에 포함되는지 확인
```
