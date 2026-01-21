# CodeVault (upcode-clone)

Ontario Building Code Part 9 검색 서비스

## 프로젝트 구조

```
upcode-clone/
├── codevault/              # Next.js 웹앱 (localhost:3001)
│   ├── src/
│   │   ├── app/            # App Router 페이지
│   │   ├── components/     # React 컴포넌트
│   │   └── lib/            # 유틸리티, 타입
│   └── public/data/        # 파싱된 JSON 데이터
│       ├── part8.json      # Part 8 데이터
│       ├── part9.json      # Part 9 데이터 (핵심)
│       ├── part9_tables.json
│       ├── part10~12.json
│       └── _archive/       # 이전 버전 보관
│
├── pipeline/               # PDF 파싱 & 변환 스크립트
│   ├── schema.sql          # SQLite 스키마
│   ├── migrate_json.py     # JSON → SQLite
│   ├── migrate_tables.py   # Tables JSON → SQLite
│   ├── parse_part9.py      # PDF 직접 파싱
│   ├── validate_part.py    # 검증 스크립트
│   └── _experiments/       # 실험용 스크립트
│
├── data/                   # 생성물 (DB)
│   └── obc.db              # SQLite 데이터베이스
│
├── source/                 # 원본 PDF
│   └── 2024 Building Code Compendium/
│       ├── 301880.pdf      # Part 9 (Housing and Small Buildings)
│       └── 301881.pdf      # Part 10-12
│
├── docs/                   # 문서
│   ├── checklist/          # 검증 체크리스트
│   ├── report/             # 작업 보고서
│   ├── adr/                # Architecture Decision Records
│   └── architecture/       # 아키텍처 문서
│
└── reference/              # 참고 자료 (UpCodes HTML 등)
```

## 데이터 파이프라인

```
┌─────────────────────────────────────────────────────────────┐
│  방법 1: JSON 기반 (권장)                                    │
├─────────────────────────────────────────────────────────────┤
│  1. python pipeline/migrate_json.py                         │
│     - schema.sql 실행 → DB 생성                             │
│     - codevault/public/data/part9.json → nodes 테이블       │
│                                                             │
│  2. python pipeline/migrate_tables.py                       │
│     - part9_tables.json → tables 테이블                     │
│                                                             │
│  3. python pipeline/add_articles_to_db.py (선택)            │
│     - Part 10, 11, 12 추가                                  │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│  방법 2: PDF 직접 파싱                                      │
├─────────────────────────────────────────────────────────────┤
│  python pipeline/parse_part9.py                             │
│     - PDF 직접 파싱 → data/obc.db 생성                      │
│     - JSON 중간 단계 없이 DB로 바로 저장                    │
└─────────────────────────────────────────────────────────────┘
```

## 빠른 시작

```bash
# 1. 의존성 설치
cd codevault
npm install

# 2. 개발 서버 실행
npm run dev  # localhost:3001

# 3. DB 재생성 (필요시)
cd ..
python pipeline/migrate_json.py
python pipeline/migrate_tables.py
```

## 기술 스택

- **Frontend**: Next.js 16, React 19, Tailwind CSS v4, TypeScript
- **Backend**: SQLite (obc.db)
- **PDF Parsing**: Python (PyMuPDF/fitz)
- **Search**: useMemo 기반 클라이언트 검색

## 문서

- `docs/checklist/` - 검증 체크리스트
- `docs/report/PDF_PARSING_GUIDE.md` - PDF 파싱 종합 가이드
- `docs/checklist/OBC_STRUCTURE_RULES.md` - OBC 계층 구조 규칙
- `CLAUDE.md` - Claude Code 작업 규칙
