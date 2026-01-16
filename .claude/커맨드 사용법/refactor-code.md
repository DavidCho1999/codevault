# /refactor-code

**코드 리팩토링 가이드**

체계적인 리팩토링 절차를 안내해줌.

## 사용법
```
/refactor-code "리팩토링 대상"
```

## 예시
```
/refactor-code "auth 모듈"
/refactor-code "API 레이어"
```

## 리팩토링 절차
1. 사전 분석 (현재 기능 파악)
2. 테스트 커버리지 확인
3. 리팩토링 전략 수립
4. 점진적 변경
5. 코드 품질 개선
6. 성능 검증
7. 문서 업데이트

## 적용 기법
- Extract Method/Function
- Extract Class/Component
- Rename Variable/Method
- Replace Conditional with Polymorphism
- Eliminate Dead Code
