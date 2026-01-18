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

---

## 참고

- OBC PDF: `source/2024 Building Code Compendium/301880.pdf`
- 레퍼런스 UI: `reference/upcode_contents1.html` (UpCodes 스타일)