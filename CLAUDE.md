# CLAUDE.md - upcode-clone 프로젝트 규칙

> Claude가 이 프로젝트에서 따라야 할 규칙

---

## 프로젝트 정보

- **프로젝트명**: CodeVault (upcode-clone)
- **목적**: Ontario Building Code Part 9 검색 서비스
- **기술 스택**: Next.js 16, React 19, Tailwind v4, TypeScript
- **상태**: 개발 중 (데이터 파싱 문제 해결 필요)

---

## 파일 구조

```
upcode-clone/
├── codevault/              # Next.js 앱 (localhost:3001)
│   ├── src/
│   │   ├── app/            # App Router 페이지
│   │   ├── components/     # React 컴포넌트
│   │   └── lib/            # 유틸리티, 타입
│   └── public/data/        # 파싱된 JSON 데이터
├── _checklist/             # 체크리스트 (검토, 할일)
│   ├── ARCHITECTURE_REVIEW_CHECKLIST.md
│   ├── E2E_PDF_PARSING_ERROR_CHECKLIST.md
│   ├── UPCODES_COMPARISON_CHECKLIST.md
│   └── todos.md
├── _report/                # 보고서 & 가이드 (참조용)
│   ├── PDF_PARSING_GUIDE.md      # PDF 파싱 종합 가이드
│   ├── CONTENT_ANALYSIS_REPORT.md
│   └── CONTENT_FIX_REPORT.md
├── scripts_temp/           # Python PDF 파싱 스크립트
├── source/                 # 원본 PDF 소스
│   └── 2024 Building Code Compendium/
│       ├── 301880.pdf      # Part 9 (Housing and Small Buildings)
│       └── 301881.pdf      # Part 10-12
├── reference/              # 참고 자료 (UpCodes HTML 등)
└── _mine/                  # 학습 자료
```

---

## 개발 규칙

1. PDF 파싱: Python (PyMuPDF/fitz)
2. 프론트엔드: Next.js 16 + TypeScript
3. 검색: useMemo 기반 클라이언트 검색
4. 스타일: Tailwind CSS v4

### PDF 파싱 가이드
- **참고 문서**: `_report/PDF_PARSING_GUIDE.md`
- PDF 파싱 작업 시 반드시 가이드 참고
- 새로운 실수/교훈 발견 시 → 가이드에 추가
- 해결방안, 코드 스니펫, 체크리스트 등 지속적으로 보완

### OBC 구조 규칙 (Building Code Specialist) ⚠️ 중요
- **참고 문서**: `_checklist/OBC_STRUCTURE_RULES.md`
- OBC 계층 구조 작업 시 **반드시** 이 문서 참고
- Claude의 추측 금지 → 실제 PDF 기반 규칙만 사용
- **핵심 포인트**:
  - 6단계 계층 아님 → **4단계 + 변형**
  - Alternative Subsection: 9.5.3A, 9.5.3B... (9.5.3의 형제!)
  - Article Suffix: 9.5.1.1A (9.5.1.1의 확장)
  - 0A Article: 9.33.6.10A (특수 케이스)
  - "Sentence" 아님 → "Clause"가 올바른 용어

---



## 사용자 정보

- 코딩 비전공자 (건축공학 전공)
- Python, Web Frontend 기초 지식
- Building Science, Structural Engineering 배경

---

## Claude 행동 규칙

## 4단계 워크플로우를 사용자가 각 단계를 진행하도록 도와주세요.
1. Research - 조사
2. Plan - 계획
3. Implement - 구현
4. Self-Validate - Claude 자체 검증 (필요하면 MCP 사용)
5. User-Validate - 사용자 검증
* 각 단계마다 컨텍스트 클리어!

### 1. 계획 먼저, 코딩은 나중
- 바로 코드 작성하지 않는다
- 먼저 접근법/계획 제시 → 사용자 동의 후 구현

### 2. 작은 단계로 반복
- 한 번에 큰 결과물 X
- 기능 하나씩, 파일 하나씩
- 컨텍스트가 많아지면 /clear 제안

### 3. 실수하면 이 파일에 기록
- 버그/실수 발생 시 → 아래 "실수 기록"에 추가
- 실수와 유사한 작업 실행 시 '문제, 증상, 원인, 해결' 참고하고 작업 진행

### 4. 검토 요청 습관화
- 코드에 버그 있을 수 있음 인정
- "확인해주세요", "검토 부탁드립니다"
- 사용자가 이해했는지 확인

### 5. 사용자 학습 돕기
- 왜 이렇게 했는지 간단히 설명
- 사용자가 이해할 수 있는 수준으로
- 전문 용어 사용 시 설명 추가

### 6. 검증 작업 시 필수 규칙 (2026-01-17 추가)
- **체크리스트 = 실행 목록** (참고용 X)
  - 체크리스트 각 단계를 **순서대로 실행**
  - 단계 건너뛰기 금지
  - 각 단계 완료 후 -> 체크리스트에 [x] 표시
- **완료 기준 명시**
  - "FINAL PASS" = 모든 컬럼이 [x] 또는 N/A
  - 하나라도 [ ]면 -> 완료 아님
- **단계별 사용자 확인**
  - 자동 검증 후 -> "수동 확인 진행할까요?" 물어보기
  - 수동 확인 없이 다음 섹션 넘어가기 금지

---

## 현재 문제점

- [ ] PDF 파싱 시 텍스트 순서 뒤섞임
- [ ] 섹션 경계 분리 실패 (9.2 내용이 9.3에 섞임)
- [ ] 일부 섹션 content 비어있음

---

## 실수 기록

### 2026-01-15: PDF 파싱 텍스트 순서 문제
- **문제**: page.get_text()로 PDF 텍스트 추출 시 순서가 뒤섞임
- **증상**: 9.1.1.7이 9.1.1.1보다 위에 표시됨
- **원인**: PDF 내부 텍스트 블록 순서 ≠ 시각적 순서
- **해결**: page.get_text("blocks") 사용 후 y좌표 → x좌표로 정렬

### 2026-01-15: PDF 섹션 경계 분리 실패
- **문제**: 여러 페이지 텍스트를 단순 연결하여 섹션 내용이 섞임
- **증상**: 9.2 Definitions 비어있고, 내용이 9.3에 포함됨
- **원인**: for p in range(page, next_page) 단순 연결
- **해결**: 섹션 ID 패턴(예: 9.2.1.)으로 정확한 경계 분리 필요

### 2026-01-17: npm run dev 실행 시 Claude Code 종료
- **문제**: 서버 실행 명령 시 Claude Code가 종료됨
- **증상**: `npm run dev` 실행 후 터미널 튕김
- **원인**: 이미 실행 중인 Next.js 프로세스와 lock 파일 충돌
- **해결**: 서버 시작 전 기존 프로세스 확인 필수
  ```bash
  # 1. 먼저 기존 프로세스 확인
  netstat -ano | findstr :3001
  # 2. 필요시 프로세스 종료
  taskkill /PID <PID> /F
  # 3. 또는 .next/dev/lock 파일 삭제
  ```

### 2026-01-17: PDF 파싱 시 섹션 내용 잘림 (Critical)
- **문제**: Subsection 내 Article 내용이 누락됨
- **증상**: 9.4.2 (Specified Loads) 섹션에서:
  - 9.4.2.1 Application의 (e), (f) 조항 누락
  - 수식 `Do = 10(Ho – 0.8 Ss / γ)` 누락
  - 9.4.2.2, 9.4.2.3 Article 전체 누락
  - Content 길이: 578자 (원본 대비 ~20%)
- **원인**: `parse_obc_v4.py`의 `extract_subsection_content()` 함수
  ```python
  # next_sub_id (9.4.3)를 발견하면 즉시 내용 종료
  if next_sub_id:
      end_pattern = rf'{re.escape(next_sub_id)}\.\s*'
  ```
  - 상위 Subsection ID만 인식 (9.4.3)
  - 내부 Article ID (9.4.2.2, 9.4.2.3) 무시
  - 수식/특수문자 영역에서 정규식 실패 가능
- **해결 방향**:
  1. Article 레벨까지 파싱 깊이 확장
  2. 다음 Subsection 대신 **같은 레벨** 다음 Article까지 파싱
  3. 수식이 포함된 텍스트 블록 특별 처리
  4. **검증 스크립트 필수**: 모든 섹션의 content 길이 체크
- **예방책**:
  - PDF 파싱 후 반드시 content 길이 검증
  - 수식/표가 많은 섹션 (9.4, 9.25 등) 수동 검토
  - 원본 PDF와 JSON 비교 자동화

### 2026-01-17: 검증 스크립트가 참조 텍스트를 Article로 오인 (Critical)
- **문제**: 자동 검증에서 "OK" 표시됐지만 실제 content가 뒤섞여 있었음
- **증상**:
  - 9.3.1.1 내용: "Articles 9.3.1.2. to 9.3.1.2. Cement" (잘못됨)
  - 원래: "Articles 9.3.1.6. and 9.3.1.7., unreinforced..." (정확)
- **원인**:
  1. 검증 패턴 `\b(9\.\d+\.\d+\.\d+)\.?\s`가 **참조 텍스트도 매칭**
  2. "Articles 9.3.1.6. and 9.3.1.7."에서 9.3.1.6을 Article로 오인
  3. `reorder_articles_in_content`가 참조를 별도 블록으로 분리 → 내용 뒤섞임
- **왜 처음에 놓쳤나**:
  - 자동 검증만 믿고 **실제 텍스트 내용 확인 안 함**
  - Article 개수/길이만 체크, **정확성은 미확인**
- **해결**:
  1. 패턴을 `\n(9\.x\.x\.x)\.\s+[A-Z]`로 변경 (줄 시작 + 대문자 제목)
  2. 참조가 아닌 실제 헤딩만 매칭
- **예방책**:
  1. 자동 검증 후 **반드시 샘플 텍스트 수동 확인**
  2. PDF 원본과 JSON content 직접 비교
  3. 검증 스크립트에 참조 패턴 제외 로직 추가
  4. "OK"로 표시되어도 최소 3개 섹션 수동 검토

### 2026-01-17: PDF 수식이 이미지로 저장되어 추출 불가 (Critical)
- **문제**: PDF의 수학 수식이 텍스트가 아닌 이미지로 저장됨
- **증상**: 9.4.2.2 (5)에서 `xd = 5(h - 0.55Ss/γ)` 수식 완전 누락
  - PDF 텍스트: "(5)...shall be calculated as follows:" → "where"
  - 수식 자체가 JSON에 없음
- **원인**: PDF 생성 시 수식을 **이미지로 삽입**
  ```
  Text at y=371: '(5) For the purposes...shall be calculated as follows:'
  Image block at: (276.95, 382.5, 371.05, 422.35)  <-- 수식 이미지!
  Text at y=423: 'where'
  ```
  - PyMuPDF의 `get_text()`는 이미지 내 텍스트 추출 불가
  - MathType, Symbol 폰트로 생성된 수식도 마찬가지
- **영향받는 섹션**: 수식이 많은 모든 섹션
  - 9.4.2 (눈 하중 계산)
  - 9.25 (열/습기 제어 - RSI 계산)
  - 9.8 (계단 치수 계산)
  - 기타 구조/열 계산 관련 섹션들
- **해결 방안**:
  1. **OCR 적용**: `page.get_text("text", flags=fitz.TEXT_PRESERVE_IMAGES)` 또는 Tesseract OCR
  2. **이미지 추출 후 OCR**: 수식 이미지만 추출 → OCR → LaTeX 변환
  3. **수동 입력**: 주요 수식 수동으로 JSON에 추가 (확실한 방법)
  4. **PDF.js + MathPix**: 고급 수식 인식 API 사용
- **당장의 해결책**: 주요 수식 수동 입력
  ```json
  "9.4.2.2.(5)": "xd = 5(h - 0.55Ss/γ)"
  "9.4.2.1.(1)(f)": "Do = 10(Ho - 0.8Ss/γ)"
  "9.4.2.2.(1)": "S = CbSs + Sr"
  ```

### 2026-01-17: end_pattern이 Subsection 헤더 형식과 불일치 (Critical)
- **문제**: `end_pattern`이 실제 PDF 텍스트 형식과 맞지 않아 content가 다음 섹션까지 포함됨
- **증상**: 9.7.1 content에 9.7.2 Article들이 포함됨 (1087자 → 435자로 수정)
- **원인 1**: 패턴 `
9.7.2.\s*
`은 `9.7.2.` 뒤에 바로 줄바꿈을 기대
  - 실제 텍스트: `
9.7.2.  Required Windows...
` (공백 + 제목)
  - 패턴 `\s*
`이 매칭 안 됨
- **원인 2**: 테이블 Notes 다음에 섹션이 시작되면 같은 줄로 연결됨
  - 실제: `...shall apply.    9.7.4.  Manufactured...` (공백 4개로 연결)
  - 줄바꿈 `
` 없음
- **해결**:
  ```python
  # 변경 전
  end_pattern = "
" + re.escape(next_sub_id) + r"\.\s*
"

  # 변경 후 (줄바꿈 또는 공백 2개 이상)
  end_pattern = r"(?:
|\s{2,})" + re.escape(next_sub_id) + r"\.\s+"
  ```
- **예방책**: PDF 텍스트 추출 후 실제 형식 확인 필수

### 2026-01-18: (a), (b) clause 줄바꿈 누락 + 문장 끝 분리 오류
- **문제**: (a), (b), (c) clause가 줄바꿈 없이 한 문단으로 연결되고, 문장 끝이 별도 블록으로 분리됨
- **증상**: 9.8.6.3.(4) 웹 렌더링에서:
  ```
  (4) ... shall be (a) where one or more... width, or (b) where all... not less than the lesser actual

  stair or ramp width.   <- 별도 줄로 분리됨 (원래 (b)의 끝부분)
  ```
- **원인**: PDF 파싱 시 clause 경계 인식 실패 + 줄바꿈 처리 오류
  - (a), (b) 등이 새 줄로 시작해야 하는데 이전 텍스트에 연결됨
  - 문장 끝부분이 잘려서 별도 `<p>` 태그로 렌더링됨
- **영향받는 섹션**: 9.8.6, 9.8.7, 9.8.8 등 clause가 많은 섹션
- **해결 방향**:
  1. 파싱 스크립트에서 `(a)`, `(b)`, `(c)` 앞에 줄바꿈 추가
  2. 또는 렌더링 컴포넌트에서 clause 패턴 인식하여 별도 처리
- **예방책**: 웹 렌더링 검증 시 clause 줄바꿈 필수 확인

### 2026-01-18: 수식 + "where" 블록 분리 실패 (Critical)
- **문제**: 수식과 "where" 키워드가 하나의 박스 안에 함께 렌더링됨
- **증상**:
  ```
  [박스] S = CbSs + Sr where
  ```
  원래는:
  ```
  [박스] S = CbSs + Sr

  where
  S = ...
  Cb = ...
  ```
- **근본 원인**: SectionView.tsx:264 전처리 로직
  ```typescript
  processedContent = processedContent.replace(/\n(?![(\d9A-Z])/g, ' ');
  ```
  이 패턴이 "where" 앞의 줄바꿈도 공백으로 변환함:
  - `\n` 뒤가 소문자 `w`라서 `[(\d9A-Z]`에 매칭 안 됨
  - 결과: `수식\nwhere` → `수식 where`로 합쳐짐

- **해결** (최종):
  ```typescript
  // SectionView.tsx:264-265
  // "where", 소문자 수식(xd=...), 그리스 문자(γ=...) 앞의 줄바꿈 유지
  processedContent = processedContent.replace(/\n(?!where\b|[a-zγ]{1,3}\s*=|[(\d9A-Z])/g, ' ');
  ```
  - `where\b` - "where" 키워드
  - `[a-zγ]{1,3}\s*=` - 소문자/그리스 문자 변수 (xd=, h=, γ=)
  - `[(\d9A-Z]` - 괄호, 숫자, 대문자

- **추가 수정 이력**:
  1. `where\b` 추가 → 수식과 where 분리
  2. `[a-z]{1,3}\s*=` 추가 → xd= 같은 소문자 수식 분리
  3. `γ` 추가 → 그리스 문자 변수 분리

- **영향 섹션**: 9.4.2.1.(1)(f), 9.4.2.2.(1), 9.4.2.2.(5) 등 수식 + where 조합
- **예방책**: 수식 렌더링 검증 시 "where" 블록이 별도로 표시되는지 확인 필수

### 2026-01-18: where 블록이 숫자로 시작하는 연속 텍스트에서 조기 종료
- **문제**: where 블록 내용 중 숫자로 시작하는 줄에서 블록이 종료됨
- **증상**: 9.4.2.2.(1)의 where 블록에서
  ```
  where
    S = specified snow load,
    Cb = basic snow load roof factor, which is 0.45 where... 4.3 m and
  ← 여기서 종료됨!

  0.55 for all other roofs,   ← where 블록 밖으로 나감
  Ss = 1-in-50 year ground...
  ```
- **원인**: SectionView.tsx의 where 블록 종료 조건이 너무 광범위
  ```typescript
  // 변경 전: 숫자나 괄호로 시작하면 모두 종료
  if (varLine.match(/^[\(\d]/) || varLine.match(/^\d+\.\d+/)) {
    break;
  }
  ```
  - `0.55 for all other roofs`가 숫자로 시작해서 종료됨
  - 실제로는 Cb 변수 설명의 연속인데 잘못 끊김

- **해결**: 종료 조건을 clause/섹션 번호로만 한정
  ```typescript
  // 변경 후: 실제 clause나 섹션 번호만 종료
  if (varLine.match(/^\(\d+\)/) ||      // (1), (2) clause
      varLine.match(/^\([a-z]\)/) ||    // (a), (b) sub-clause
      varLine.match(/^9\.\d+\.\d+/)) {  // 9.x.x 섹션 번호
    break;
  }
  ```

- **수정 위치**: SectionView.tsx 471-474번 줄, 634-637번 줄 (2곳)
- **예방책**: where 블록 검증 시 모든 변수 정의가 블록 안에 포함되는지 확인

### 2026-01-18: OBC 계층 구조 잘못 이해 (Critical)
- **문제**: Claude가 OBC 구조를 추측하여 틀린 6단계 계층을 문서화함
- **증상**:
  - 문서에 "6단계: Part → Section → Subsection → Article → Sentence → Clause → Subclause"라고 씀
  - 실제 PDF에는 9.5.3A, 9.5.1.1A, 9.33.6.10A 같은 변형 패턴 존재
  - "Sentence"는 OBC 용어가 아님 (실제는 "Clause")
- **원인**:
  - 실제 PDF를 확인하지 않고 추측으로 문서 작성
  - 일부 예시만 보고 전체 구조를 일반화
- **실제 구조**:
  ```
  4단계 + 변형:
  - Section: 9.X
  - Subsection: 9.X.X 또는 9.X.X[A-Z] (Alternative)
  - Article: 9.X.X.X 또는 9.X.X.X[A-Z] 또는 9.X.X[A-Z].X (Sub-Article)
  - Clause: (1), (2)... → Sub-clause: (a), (b)...
  ```
- **해결**: `_checklist/OBC_STRUCTURE_RULES.md` 생성 (PDF 분석 기반)
- **예방책**:
  1. OBC 구조 관련 작업 시 반드시 `OBC_STRUCTURE_RULES.md` 참고
  2. Claude의 추측 금지 → 실제 PDF 기반 규칙만 사용
  3. 새로운 패턴 발견 시 → 규칙 문서에 추가

### 2026-01-18: 테이블 MERGE 구조 검증 누락 (Critical)
- **문제**: 테이블의 rowspan/colspan 병합 구조를 확인하지 않고 "완료"로 판단
- **증상**: Table 9.4.3.1에서 첫 번째 열이 빈 셀로 처리됨
  - PDF: "Roof rafters..." 셀이 3행 병합 (rowspan=3)
  - HTML: `<th>Roof rafters...</th>` + `<th></th>` + `<th></th>` (빈 셀!)
  - 웹에서 구조가 깨져 보임
- **원인**:
  - 자동 변환(Camelot)이 복잡한 병합 인식 못함
  - 품질 체크리스트에서 "caption 존재", "source 필드"만 확인
  - **MERGE 구조 확인을 건너뜀!**
- **해결**:
  1. PDF 이미지 추출하여 원본 구조 파악
  2. HTML의 rowspan/colspan 개수 확인
  3. 빈 `<th></th>` 셀 없는지 확인
  4. 불일치 시 완전한 data + spans 오버라이드
- **예방책**:
  - 테이블 검증 시 **항상** PDF 이미지 먼저 추출
  - rowspan/colspan 개수가 PDF와 일치하는지 확인
  - 품질 체크리스트에 🔴 MERGE 항목 추가됨

### 2026-01-18: clean_text() 패턴이 콘텐츠를 삭제함 (Critical)
- **문제**: `clean_text()` 함수의 헤더/푸터 제거 패턴이 너무 광범위하여 실제 콘텐츠까지 삭제
- **증상**: 9.1.1.1, 9.2.1.1 등의 Article에 content가 없음
  - 9.2 Definitions 섹션 전체가 웹에서 비어있음
- **원인**:
  ```python
  # 문제의 패턴
  text = re.sub(r'^.*Division [ABC].*$', '', text, flags=re.MULTILINE)
  ```
  이 패턴이 "Division A", "Division B", "Division C"를 **언급**하는 모든 줄을 삭제
  - 예: `(1) The application of this Part shall be as described in Subsection 1.3.3. of Division A.`
  - 이 줄이 "Division A"를 포함하여 삭제됨
- **해결**:
  ```python
  # 수정된 패턴 - 헤더/푸터만 정확히 매칭
  text = re.sub(r'^\d{4}\s+Building Code.*$', '', text, flags=re.MULTILINE)
  text = re.sub(r'^Division [ABC]\s*-\s*Part\s*\d+.*$', '', text, flags=re.MULTILINE)
  ```
- **예방책**:
  1. 정규식 패턴은 **가능한 한 구체적으로** 작성
  2. `.*` 같은 광범위한 패턴 사용 시 주의
  3. 패턴 변경 후 **샘플 콘텐츠로 테스트** 필수
  4. 특정 키워드로 필터링 시 **콘텐츠에서도 해당 키워드가 사용되는지** 확인

### 2026-01-20: 한 줄짜리 HTML 테이블 처리 버그 (Critical)
- **문제**: `<table>...</table>`이 한 줄에 있어도 `</table>`을 찾을 때까지 다음 줄들을 계속 읽음
- **증상**: Table 11.2.1.1.-F 헤딩이 렌더링되지 않고 마크다운 텍스트로 표시됨
  - `#### Table 11.2.1.1.-F **(1) Hazard Index**...` 가 plain text로 나타남
- **원인**: SectionView.tsx의 HTML 테이블 처리 로직
  ```typescript
  if (trimmed.startsWith('<table')) {
    const tableLines = [trimmed];
    i++;
    while (i < lines.length) {
      tableLines.push(lines[i]);
      i++;
      if (lines[i].includes('</table>')) break;  // 첫 줄 체크 안 함!
    }
  }
  ```
  - 첫 줄에 `</table>`이 있어도 다음 줄을 계속 읽어 `i` 과도하게 증가
  - 결과: 다음 테이블 헤딩(`#### Table 11.2.1.1.-F`)을 건너뜀
- **해결**:
  ```typescript
  if (!trimmed.includes('</table>')) {
    // 여러 줄 테이블만 다음 줄 읽기
  } else {
    i++;  // 한 줄 테이블은 바로 다음으로
  }
  ```
- **예방책**: HTML 태그 처리 시 **한 줄 완결 케이스** 항상 먼저 확인

### 2026-01-20: PDF 테이블 페이지 분리로 인한 구조 손실 (Critical)
- **문제**: 긴 테이블이 페이지 경계에서 분리될 때 두 번째 부분이 flat text로 저장됨
- **증상**: C161~C174가 테이블이 아닌 연속 텍스트로 표시됨
  - `C.A. Number Division B Requirements Compliance Alternative C161 9.10.13.2.(1) In a building...`
- **원인**: PDF 파싱 시 페이지 나눔 후 테이블 컨텍스트 손실
- **해결**: flat text를 정규식으로 파싱 후 HTML `<table>` 변환
- **예방책**:
  1. 파싱 후 flat text 테이블 패턴 감지 스크립트 실행
  2. Part 11 Table 11.5.1.1 시리즈 수동 검토
  3. `<table>` 태그 없이 "C.A. Number", "H.I." 등 헤더가 있으면 경고

---

## 참고

- OBC PDF: `source/2024 Building Code Compendium/301880.pdf`
- 레퍼런스 UI: `reference/upcode_contents1.html` (UpCodes 스타일)