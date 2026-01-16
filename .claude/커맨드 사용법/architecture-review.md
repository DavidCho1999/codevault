# /architecture-review

**아키텍처 리뷰**

현재 코드베이스의 구조, 패턴, 의존성을 종합 분석.

## 사용법
```
/architecture-review
/architecture-review --modules
/architecture-review --patterns
/architecture-review --dependencies
/architecture-review --security
```

## 옵션 설명
- `--modules`: 모듈 구조 분석
- `--patterns`: 디자인 패턴 평가
- `--dependencies`: 의존성 및 커플링 분석
- `--security`: 보안 아키텍처 검토

## 분석 항목
- 컴포넌트 계층 구조
- 안티패턴 탐지
- 순환 의존성 확인
- 확장성/성능 평가
