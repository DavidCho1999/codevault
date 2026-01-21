# Canadian Building Code MCP - Project Plan

> "Map & Territory" 아키텍처를 활용한 저작권 안전 Building Code MCP

---

## 프로젝트 개요

### 핵심 컨셉

```
"나는 '지도(Map)'만 줄게, '땅(PDF)'은 네가 가져와."
```

**기존 방식의 문제:**
- 텍스트 배포 → 저작권 침해 위험
- 허가 필요 → 시간/비용 소요
- 거절 시 → 프로젝트 중단

**새로운 방식 (좌표 오버레이):**
- 좌표/구조만 배포 → 저작권 우회
- 텍스트는 사용자 PDF에서 추출
- 법적 안전 + 빠른 속도

---

## 아키텍처

```
┌─────────────────────────────────────────────────────────────┐
│                    개발자 (동제) 측                          │
├─────────────────────────────────────────────────────────────┤
│  [OBC PDF] → [Marker 파싱] → [좌표 추출] → [structure_map.json] │
│                              (시간 소요)      (배포물)           │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ 배포 (GitHub)
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      사용자 측                               │
├─────────────────────────────────────────────────────────────┤
│  [사용자 PDF] + [structure_map.json]                         │
│       │              │                                       │
│       ▼              ▼                                       │
│  [PyMuPDF] ←── [좌표로 위치 지정]                             │
│       │                                                      │
│       ▼                                                      │
│  [텍스트 추출] → [로컬 DB 생성] → [MCP 서버] → [Claude]       │
│  (10초)          (자동)          (실행)                       │
└─────────────────────────────────────────────────────────────┘
```

---

## 법적 분석

### 배포하는 것 (안전)

| 데이터 | 예시 | 저작권 |
|--------|------|--------|
| 페이지 번호 | `"page": 245` | 사실(fact) - 보호 안 됨 |
| 좌표 | `"bbox": [50, 100, 400, 300]` | 숫자 - 보호 안 됨 |
| Section ID | `"id": "9.8.2.1"` | 참조 번호 - 보호 안 됨 |
| 구조 타입 | `"type": "article"` | 분류 - 보호 안 됨 |

### 배포하지 않는 것

| 데이터 | 저작권 |
|--------|--------|
| 조문 텍스트 | 저작권 보호 대상 |
| 테이블 데이터 | 저작권 보호 대상 |
| 수식 내용 | 저작권 보호 대상 |

### 법적 논거

```
1. 좌표는 "사실(fact)"이지 "창작물"이 아님
2. "9.8.2.1이 245페이지에 있다" = 객관적 사실
3. 저작권법은 "창작적 표현" 보호, "사실" 보호 안 함
4. 텍스트 복제 없음 = 침해 핵심 요소 없음
```

### 리스크 평가

| 방식 | 리스크 수준 |
|------|-------------|
| 텍스트 배포 | 🔴 높음 (확실한 저작권 문제) |
| 좌표만 배포 | 🟢 매우 낮음 (99% 안전) |

---

## 지원 코드 목록

### Phase 1: Ontario Building Code (확실히 가능)

| 코드 | 상태 | 비고 |
|------|------|------|
| OBC 2024 | ✅ 가능 | PDF 내 "비상업적 사용" 명시 |

### Phase 2: National Building Code (허가 or 좌표 방식)

| 코드 | 방법 |
|------|------|
| NBC 2020/2025 | NRC 허가 요청 또는 좌표 방식 |
| Manitoba, Saskatchewan, NS, NB, PEI, Yukon, NWT, Nunavut | NBC 채택 → NBC 커버 시 자동 커버 |

### Phase 3: 주별 코드

| 코드 | 연락처 | 방법 |
|------|--------|------|
| BC Building Code | ipp@mail.qp.gov.bc.ca | 허가 요청 또는 좌표 방식 |
| Alberta Edition | NRC | NBC 허가에 포함 가능 |
| Quebec | NRC + Quebec | 별도 확인 필요 |

---

## 기술 스택

```
개발자 측 (파싱):
├── Marker (PDF → 구조 분석)
├── PyMuPDF (좌표 추출 보조)
└── Python (structure_map.json 생성)

사용자 측 (MCP):
├── Python MCP SDK
├── PyMuPDF (빠른 텍스트 추출)
├── SQLite (로컬 DB)
└── hashlib (PDF 버전 검증)
```

---

## 파일 구조

```
canadian-building-code-mcp/
├── README.md                 # 설치/사용 가이드
├── LICENSE                   # MIT 또는 Apache 2.0
├── requirements.txt          # 의존성
│
├── maps/                     # 좌표 맵 (배포물)
│   ├── obc_2024_map.json    # Ontario Building Code
│   ├── nbc_2025_map.json    # National Building Code
│   └── checksums.json        # PDF 해시값
│
├── src/
│   ├── mcp_server.py        # MCP 서버 메인
│   ├── pdf_extractor.py     # PyMuPDF 텍스트 추출
│   ├── db_builder.py        # 로컬 DB 생성
│   └── utils.py             # 유틸리티
│
└── docs/
    ├── LEGAL.md             # 법적 고지
    └── ARCHITECTURE.md      # 아키텍처 설명
```

---

## 관련 문서

- [01_ARCHITECTURE.md](./01_ARCHITECTURE.md) - 상세 아키텍처
- [02_IMPLEMENTATION.md](./02_IMPLEMENTATION.md) - 구현 가이드
- [03_LEGAL.md](./03_LEGAL.md) - 법적 분석
- [04_ROADMAP.md](./04_ROADMAP.md) - 개발 로드맵
- [05_USER_GUIDE.md](./05_USER_GUIDE.md) - 사용자 가이드

---

## 연락처

### 허가 요청 (선택적)

| 대상 | 이메일 |
|------|--------|
| NRC (National) | Codes@nrc-cnrc.gc.ca |
| BC | ipp@mail.qp.gov.bc.ca |
| Ontario | buildingtransformation@ontario.ca |

---

## 참고

- 이 프로젝트는 교육/공익 목적의 비상업적 프로젝트입니다
- 모든 저작권은 원 저작권자에게 있습니다
- 좌표 정보만 배포하며, 실제 콘텐츠는 사용자가 합법적으로 취득한 PDF에서 추출됩니다
