# ADR-005: Tailwind CSS v4 선택

## 상태
Accepted

## 맥락

CodeVault의 스타일링 방식을 결정해야 했습니다.

### 요구사항
- 빠른 개발 속도
- 일관된 디자인 시스템
- 작은 프로덕션 번들 크기
- 반응형 디자인 지원
- 다크 모드 지원 가능성

### 프로젝트 특성
- 문서 중심 UI (읽기 최적화)
- 컴포넌트 수 적음 (~10개)
- 디자인 복잡도 낮음
- 개발자 1인 프로젝트

## 결정

**Tailwind CSS v4를 PostCSS 플러그인으로 사용한다.**

```javascript
// postcss.config.mjs
export default {
  plugins: {
    '@tailwindcss/postcss': {},
  },
};
```

```css
/* globals.css */
@import "tailwindcss";

:root {
  --background: #ffffff;
  --foreground: #171717;
}
```

```tsx
// 사용 예시
<div className="flex flex-col gap-4 p-6 bg-white rounded-lg shadow-md">
  <h1 className="text-2xl font-bold text-gray-900">Title</h1>
  <p className="text-gray-600 leading-relaxed">Content</p>
</div>
```

## 선택지

### 선택지 1: Tailwind CSS v4 ✓ 선택됨
- **장점**:
  - Utility-first로 빠른 개발
  - 자동 PurgeCSS (작은 번들)
  - 우수한 DX (자동완성)
  - v4 최신 기능 (CSS 변수 통합)
  - 커뮤니티 생태계
- **단점**:
  - HTML에 클래스가 많아짐
  - 학습 곡선 (유틸리티 클래스 암기)
  - v4는 아직 새로운 버전

### 선택지 2: CSS Modules
- **장점**:
  - 스코프된 CSS
  - 순수 CSS 문법
  - 번들러 통합
- **단점**:
  - 파일 증가 (`.module.css`)
  - 클래스 네이밍 필요
  - 유틸리티 클래스 직접 작성

### 선택지 3: styled-components / Emotion
- **장점**:
  - CSS-in-JS
  - 동적 스타일링
  - 컴포넌트 스코프
- **단점**:
  - 런타임 오버헤드
  - SSR 설정 복잡
  - 번들 크기 증가

### 선택지 4: Vanilla CSS
- **장점**:
  - 의존성 없음
  - 완전한 제어
  - 표준 기술
- **단점**:
  - 수동 작업 많음
  - 일관성 유지 어려움
  - PurgeCSS 직접 설정

### 선택지 5: Chakra UI / shadcn/ui
- **장점**:
  - 완성된 컴포넌트
  - 접근성 내장
  - 빠른 프로토타이핑
- **단점**:
  - 커스터마이징 제한
  - 번들 크기 증가
  - 디자인 종속성

## 결과

### 긍정적
- 개발 속도 향상 (클래스 조합으로 빠른 스타일링)
- 프로덕션 CSS ~10KB (사용된 클래스만 포함)
- 반응형 디자인 간편 (`md:`, `lg:` 프리픽스)
- 다크 모드 추가 용이 (`dark:` 프리픽스)
- VS Code 자동완성으로 생산성 향상

### 부정적
- HTML 태그에 긴 클래스 목록
- Tailwind 유틸리티 클래스 학습 필요
- 복잡한 애니메이션에는 추가 CSS 필요

### 사용 패턴

```tsx
// 레이아웃
<div className="flex h-screen">
  <aside className="w-64 fixed">Sidebar</aside>
  <main className="flex-1 ml-64">Content</main>
</div>

// 카드 컴포넌트
<div className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow">
  <h2 className="text-xl font-semibold mb-2">Title</h2>
  <p className="text-gray-600">Description</p>
</div>

// 반응형
<div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
  {items.map(item => <Card key={item.id} {...item} />)}
</div>
```

## 참고
- [Tailwind CSS v4 Documentation](https://tailwindcss.com/docs)
- [Tailwind CSS v4 Announcement](https://tailwindcss.com/blog/tailwindcss-v4-alpha)
- [PostCSS Integration](https://tailwindcss.com/docs/installation/using-postcss)
