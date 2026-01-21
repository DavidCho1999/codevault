# Part 9 Content 수정 보고서
일시: 2026-01-17

---

## 문제 발견

PDF 파싱 시 섹션 내용이 잘려서 저장됨 (수식, Article 누락)

### 원인
- `parse_obc_v4.py`의 `extract_subsection_content()` 함수
- 다음 Subsection ID를 발견하면 즉시 종료 (내부 Article 무시)
- 수식/특수문자 영역에서 정규식 실패

---

## 수정된 섹션

| Section ID | Title | 수정 전 | 수정 후 | 증가율 |
|------------|-------|---------|---------|--------|
| 9.4.2 | Specified Loads | 578자 | 3754자 | 6.5x |
| 9.8.3 | Stair Configurations | 103자 | 1017자 | 9.9x |
| 9.10.14 | Spatial Separation Between Buildings | 148자 | 11101자 | 75.0x |
| 9.7.3 | Performance of Windows, Doors and Skylights | 426자 | 4446자 | 10.4x |

---

## 복구된 내용 (9.4.2 예시)

### 수정 전 (잘린 내용)
```
9.4.2.1. Application
(1) ... (a)~(d) 조항만
```

### 수정 후 (전체 내용)
```
9.4.2.1. Application
  (1) (a)~(f) 조항 전체
  수식: Do = 10(Ho – 0.8 Ss / γ)
  where 블록 전체
9.4.2.2. Specified Snow Loads
  S = CbSs + Sr 수식 포함
9.4.2.3. Platforms Subject to Snow and Occupancy Loads
9.4.2.4. Attics and Roof Spaces
```

---

## 남은 짧은 섹션 (참고)

일부 섹션은 원본 PDF에서도 짧음 (정상):
- `9.31.5 Reserved`: 16자 (실제로 예약된 빈 섹션)
- `9.14.3 Drainage Tile and Pipe`: 참조만 있는 짧은 섹션

---

## 검증 방법

1. 웹에서 http://localhost:3001/code/9.4.2 접속
2. 9.4.2.1 (a)~(f) 조항 확인
3. 수식 `Do = 10(Ho – 0.8 Ss / γ)` 표시 확인
4. 9.4.2.2, 9.4.2.3, 9.4.2.4 Article 존재 확인

---

## 예방책 (CLAUDE.md에 기록됨)

1. PDF 파싱 후 모든 섹션 content 길이 검증
2. 500자 미만 섹션 자동 경고
3. 수식이 많은 섹션 (9.4, 9.25) 수동 검토
4. 원본 PDF와 JSON 비교 자동화
