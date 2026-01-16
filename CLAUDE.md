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

### 4. 검토 요청 습관화
- 코드에 버그 있을 수 있음 인정
- "확인해주세요", "검토 부탁드립니다"
- 사용자가 이해했는지 확인

### 5. 사용자 학습 돕기
- 왜 이렇게 했는지 간단히 설명
- 사용자가 이해할 수 있는 수준으로
- 전문 용어 사용 시 설명 추가

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

---

## 참고

- OBC PDF: `source/2024 Building Code Compendium/301880.pdf`
- 레퍼런스 UI: `reference/upcode_contents1.html` (UpCodes 스타일)