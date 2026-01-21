# 폴더 정리안 (Draft)

## 목적
- 원본/중간/최종 산출물 분리
- 실험용 스크립트와 공식 파이프라인 구분
- 웹앱과 데이터 파이프라인의 경계 명확화

## 제안 구조 (상위)
```
/data
  /raw            # 원본 PDF
  /interim        # marker/md 등 중간 산출물
  /processed      # 최종 JSON, search index
  /archive        # 실험/버전별 결과
  /db             # sqlite 등

/pipeline
  /scripts        # 공식 파이프라인 스크립트
  /experiments    # 임시/실험 스크립트

/apps
  /web            # Next.js 웹앱 (현재 codevault)

/docs             # 아키텍처/ADR/가이드
/reports          # 검증 리포트
/notes            # 개인 메모 (공유 시 제외)
```

## 현재 폴더 -> 제안 폴더 매핑
- `source/` -> `data/raw/`
- `scripts/` -> `pipeline/scripts/`
- `scripts_temp/` -> `pipeline/experiments/`
- `codevault/` -> `apps/web/`
- `codevault/public/data/*.json` -> `data/processed/`
- `obc.db` -> `data/db/`
- `_report/` -> `reports/`
- `_checklist/` -> `docs/checklists/` 또는 `reports/`
- `_mine/` -> `notes/` (공유 제외 권장)
- `reference/` -> `docs/reference/`

## 데이터 흐름 (요약)
1) `data/raw/*.pdf`
2) `pipeline/scripts/*` 실행
3) `data/interim/*` 생성 (marker/md, 테이블 중간 산출물)
4) 검증/정규화
5) `data/processed/*.json` 생성
6) `apps/web`에서 `data/processed`를 읽어 서비스

## 정리 기준
- `data/processed`에는 배포용 최종 산출물만 유지
- 버전 테스트 결과는 `data/archive`로 이동
- 실험 스크립트는 `pipeline/experiments`로 이동
- 공개 저장소라면 `notes/` 및 개인 설정 폴더는 제외

## 권장 파일/문서
- 루트 `README.md`: 전체 파이프라인, 실행 순서, 산출물 설명
- `docs/`: 파이프라인/아키텍처/검증 기준 정리
- `apps/web/README.md`: 웹앱 실행 방법만 간단히

## 간단한 마이그레이션 순서 (예시)
1) 새 폴더 생성 (`data`, `pipeline`, `apps`, `docs`, `reports`, `notes`)
2) 큰 단위 폴더 이동
3) `codevault/public/data`에서 최종 JSON만 `data/processed`로 이동
4) 웹앱에서 경로 변경 (정적 파일 참조 경로 업데이트)
5) `.gitignore`에 중간 산출물/실험 결과 제외 규칙 추가

---

원하면 이 구조로 실제 이동/경로 수정까지 바로 진행할게.
