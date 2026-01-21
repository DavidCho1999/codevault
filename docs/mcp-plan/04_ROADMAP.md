# 04. Roadmap - 개발 로드맵

## 전체 타임라인

```
Phase 0: 준비 ────────────────┐
                              │
Phase 1: OBC MVP ─────────────┼── 1주차
                              │
Phase 2: 검증 & 개선 ─────────┼── 2주차
                              │
Phase 3: NBC 확장 ────────────┼── 3주차
                              │
Phase 4: 다중 코드 지원 ──────┼── 4주차+
                              │
Phase 5: 배포 & 문서화 ───────┘
```

---

## Phase 0: 준비 (1-2일)

### 목표
- 프로젝트 구조 설정
- 필요 도구 확인
- Marker bbox 출력 검증

### 체크리스트

- [ ] GitHub 저장소 생성
- [ ] 기본 디렉토리 구조 생성
- [ ] Marker bbox 출력 테스트
- [ ] PyMuPDF clip 기능 테스트
- [ ] 개발 환경 문서화

### 핵심 검증

```python
# Marker bbox 테스트
# data/marker/chunk_01/301880/301880_meta.json에서
# polygon 데이터가 실제로 사용 가능한지 확인

import fitz
doc = fitz.open("source/.../301880.pdf")
page = doc[0]  # 첫 페이지

# meta.json의 polygon을 rect로 변환
polygon = [[66.6, 42.5], [254.0, 42.5], [254.0, 70.6], [66.6, 70.6]]
rect = fitz.Rect(polygon[0][0], polygon[0][1], polygon[2][0], polygon[2][1])

text = page.get_text("text", clip=rect)
print(text)  # "Ministry of..." 출력되어야 함
```

---

## Phase 1: OBC MVP (3-5일)

### 목표
- Ontario Building Code structure_map 생성
- 기본 MCP 서버 구현
- 로컬 테스트 완료

### Week 1 Tasks

#### Day 1-2: 맵 생성

- [ ] `generate_map.py` 작성
- [ ] Marker 출력에서 좌표 추출 로직 구현
- [ ] Section ID 파싱 로직 구현
- [ ] `obc_2024_map.json` 생성

#### Day 3: 추출기 구현

- [ ] `extractor.py` 작성
- [ ] Fast Mode (bbox 기반) 구현
- [ ] Slow Mode (패턴 매칭) 구현
- [ ] PDF 해시 검증 구현

#### Day 4: DB & MCP 서버

- [ ] `database.py` 작성
- [ ] SQLite 스키마 구현
- [ ] FTS5 검색 구현
- [ ] `server.py` MCP 서버 구현

#### Day 5: 통합 테스트

- [ ] End-to-end 테스트
- [ ] Claude Desktop 연동 테스트
- [ ] 버그 수정

### 산출물

```
maps/
├── obc_2024_map.json     # ~500KB
└── checksums.json        # ~1KB

src/
├── server.py
├── extractor.py
├── database.py
└── config.py
```

---

## Phase 2: 검증 & 개선 (3-5일)

### 목표
- 추출 정확도 검증
- 누락 섹션 보완
- 성능 최적화

### Tasks

#### 검증

- [ ] 전체 섹션 추출 테스트
- [ ] 테이블 추출 검증
- [ ] 수식 영역 처리 확인
- [ ] 다중 페이지 콘텐츠 처리

#### 보완

- [ ] 누락된 섹션 수동 추가
- [ ] 테이블 특수 처리 로직
- [ ] 에러 핸들링 강화

#### 최적화

- [ ] 추출 속도 측정 및 개선
- [ ] 메모리 사용량 최적화
- [ ] 캐싱 전략 구현

### 품질 기준

| 항목 | 목표 |
|------|------|
| 섹션 커버리지 | > 95% |
| 추출 정확도 | > 98% |
| 설정 시간 | < 2분 |
| 검색 응답 | < 1초 |

---

## Phase 3: NBC 확장 (3-5일)

### 목표
- National Building Code 지원 추가
- 다중 코드 아키텍처 검증

### 선행 조건

```
Option A: NRC 허가 받음 → 텍스트 직접 저장 가능
Option B: 허가 없음 → 좌표 방식으로 진행
```

### Tasks

- [ ] NBC PDF 획득 (NRC 아카이브)
- [ ] Marker로 NBC 파싱
- [ ] `nbc_2025_map.json` 생성
- [ ] 다중 코드 검색 로직 구현
- [ ] 코드 간 상호 참조 기능

### 구조 변경

```python
# 다중 코드 지원
@server.tool()
async def search_code(
    query: str,
    codes: list = ["OBC", "NBC"],  # 다중 코드 검색
    province: str = None           # 주별 필터
) -> str:
    ...
```

---

## Phase 4: 다중 코드 지원 (1주+)

### 목표
- BC, Alberta, Quebec 코드 추가
- 코드 비교 기능 구현

### 우선순위

| 순위 | 코드 | 이유 |
|------|------|------|
| 1 | NBC | 8개 주 커버 |
| 2 | BCBC | 캐나다 3번째 큰 주 |
| 3 | ABC (Alberta) | 에너지 산업 중심지 |
| 4 | QCC (Quebec) | 불어권, 별도 시장 |

### 고급 기능

```python
@server.tool()
async def compare_codes(
    section_id: str,
    codes: list = ["OBC", "NBC"]
) -> str:
    """
    여러 코드 간 동일 섹션 비교
    예: "9.8.2.1 OBC vs NBC 차이점"
    """
    ...

@server.tool()
async def get_provincial_requirements(
    topic: str,
    province: str
) -> str:
    """
    특정 주의 요구사항 조회
    예: "Ontario 에너지 효율 요구사항"
    """
    ...
```

---

## Phase 5: 배포 & 문서화 (3-5일)

### 목표
- GitHub 공개 배포
- 사용자 문서 완성
- 커뮤니티 피드백 수집

### Tasks

#### 문서화

- [ ] README.md (설치 가이드)
- [ ] CONTRIBUTING.md
- [ ] API 문서
- [ ] 튜토리얼 영상/GIF

#### 배포

- [ ] PyPI 패키지 등록 (선택)
- [ ] GitHub Releases 생성
- [ ] Anthropic MCP 레지스트리 등록 (가능하면)

#### 홍보

- [ ] Reddit (r/architecture, r/engineering)
- [ ] LinkedIn 포스트
- [ ] Anthropic Discord/Forum

---

## 마일스톤 요약

| 마일스톤 | 목표 날짜 | 산출물 |
|----------|----------|--------|
| **M1: OBC MVP** | +1주 | 작동하는 OBC MCP |
| **M2: 검증 완료** | +2주 | 95% 커버리지 달성 |
| **M3: NBC 추가** | +3주 | 다중 코드 지원 |
| **M4: 공개 배포** | +4주 | GitHub v1.0 릴리스 |

---

## 리스크 & 대응

| 리스크 | 확률 | 대응 |
|--------|------|------|
| Marker bbox 불완전 | 중간 | PyMuPDF로 보완 |
| PDF 버전 다양성 | 높음 | 여러 해시 지원 |
| NRC 허가 거절 | 낮음 | 좌표 방식으로 진행 |
| 성능 문제 | 낮음 | 캐싱, 인덱싱 최적화 |

---

## 다음 문서

→ [05_USER_GUIDE.md](./05_USER_GUIDE.md) - 사용자 가이드
