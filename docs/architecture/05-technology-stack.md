# Technology Stack

> 프로젝트에서 사용하는 모든 기술과 그 선택 이유

---

## Stack Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                          TECHNOLOGY STACK                                    │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         FRONTEND                                       │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐   │  │
│  │  │  Next.js    │  │   React     │  │ TypeScript  │  │  Tailwind   │   │  │
│  │  │   16.1.2    │  │   19.2.3    │  │     5.x     │  │    CSS v4   │   │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘   │  │
│  │  ┌─────────────┐  ┌─────────────┐                                      │  │
│  │  │   KaTeX     │  │react-katex  │                                      │  │
│  │  │  0.16.27    │  │   3.1.0     │                                      │  │
│  │  └─────────────┘  └─────────────┘                                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                        BUILD TOOLS                                     │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                    │  │
│  │  │   ESLint    │  │  PostCSS    │  │    npm      │                    │  │
│  │  │     9.x     │  │  (config)   │  │  (package)  │                    │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                     DATA PROCESSING (Build-time)                       │  │
│  │  ┌─────────────┐  ┌─────────────┐                                      │  │
│  │  │   Python    │  │  PyMuPDF    │                                      │  │
│  │  │    3.x      │  │  >= 1.24.0  │                                      │  │
│  │  └─────────────┘  └─────────────┘                                      │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Frontend Technologies

### Next.js 16.1.2

| 속성 | 값 |
|------|-----|
| **역할** | Full-stack React 프레임워크 |
| **선택 이유** | React 19 지원, App Router, SSG/SSR, 최신 기능 |
| **주요 기능** | Static Generation, File-based Routing, Image Optimization |

**사용 기능:**
- App Router (`src/app/`)
- Static Site Generation (`generateStaticParams`)
- Catch-all Routes (`[...section]`)
- `next/font` (Geist fonts)
- `next/link` (Client navigation)

```typescript
// next.config.ts
import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  // 필요시 설정 추가
};

export default nextConfig;
```

### React 19.2.3

| 속성 | 값 |
|------|-----|
| **역할** | UI 라이브러리 |
| **선택 이유** | 최신 버전, Concurrent features, Server Components |
| **주요 기능** | Hooks, Server/Client Components, Suspense |

**사용 패턴:**
```typescript
// Client Component
"use client";
import { useState, useMemo } from 'react';

// Server Component (default in App Router)
export default function Page() {
  // Server-side rendering
}
```

### TypeScript 5.x

| 속성 | 값 |
|------|-----|
| **역할** | Type-safe JavaScript |
| **선택 이유** | 타입 안전성, IDE 지원, 리팩토링 용이 |
| **설정** | Strict mode, Path aliases |

```json
// tsconfig.json (주요 설정)
{
  "compilerOptions": {
    "target": "ES2017",
    "lib": ["dom", "dom.iterable", "esnext"],
    "strict": true,
    "moduleResolution": "bundler",
    "paths": {
      "@/*": ["./src/*"]
    }
  }
}
```

### Tailwind CSS v4

| 속성 | 값 |
|------|-----|
| **역할** | Utility-first CSS 프레임워크 |
| **선택 이유** | 빠른 개발, 작은 번들, 일관된 디자인 |
| **설정** | PostCSS 통합 |

```javascript
// postcss.config.mjs
export default {
  plugins: {
    '@tailwindcss/postcss': {},
  },
};
```

**사용 예시:**
```tsx
<div className="flex flex-col gap-4 p-6 bg-white rounded-lg shadow-md">
  <h1 className="text-2xl font-bold text-gray-900">Title</h1>
  <p className="text-gray-600">Content</p>
</div>
```

### KaTeX 0.16.27 + react-katex 3.1.0

| 속성 | 값 |
|------|-----|
| **역할** | LaTeX 수학 공식 렌더링 |
| **선택 이유** | MathJax보다 빠름, 작은 번들 크기 |
| **대안** | MathJax (느림), 이미지 (접근성 문제) |

**사용 예시:**
```tsx
import { BlockMath, InlineMath } from 'react-katex';
import 'katex/dist/katex.min.css';

// 인라인 수식
<InlineMath math="R = \frac{1}{U}" />

// 블록 수식
<BlockMath math="A = \pi r^2" />
```

---

## Build Tools

### ESLint 9.x

| 속성 | 값 |
|------|-----|
| **역할** | 코드 품질 검사 |
| **설정** | Flat config, Next.js presets |

```javascript
// eslint.config.mjs
import { dirname } from "path";
import { fileURLToPath } from "url";
import { FlatCompat } from "@eslint/eslintrc";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

const compat = new FlatCompat({
  baseDirectory: __dirname,
});

const eslintConfig = [
  ...compat.extends("next/core-web-vitals", "next/typescript"),
  {
    ignores: [".next/", "out/", "build/", "next-env.d.ts"],
  },
];

export default eslintConfig;
```

### PostCSS

| 속성 | 값 |
|------|-----|
| **역할** | CSS 변환 |
| **플러그인** | @tailwindcss/postcss |

---

## Data Processing (Build-time)

### Python 3.x

| 속성 | 값 |
|------|-----|
| **역할** | PDF 데이터 추출 |
| **위치** | `scripts_temp/` |
| **실행** | 수동 (빌드 전) |

### PyMuPDF (fitz) >= 1.24.0

| 속성 | 값 |
|------|-----|
| **역할** | PDF 파싱 |
| **선택 이유** | 빠른 성능, 신뢰성 있는 텍스트 추출 |
| **대안** | pdf2image (이미지 기반), pdfminer (느림) |

**사용 예시:**
```python
import fitz  # PyMuPDF

doc = fitz.open("301880.pdf")
toc = doc.get_toc()  # 목차 추출
page = doc[0]
text = page.get_text()  # 텍스트 추출
```

---

## Version Matrix

| Package | Version | Min Node | Purpose |
|---------|---------|----------|---------|
| next | 16.1.2 | 18.17.0 | Framework |
| react | 19.2.3 | 18.17.0 | UI Library |
| react-dom | 19.2.3 | 18.17.0 | DOM Rendering |
| typescript | ^5 | - | Type Safety |
| tailwindcss | ^4 | - | CSS Framework |
| katex | ^0.16.27 | - | Math Rendering |
| react-katex | ^3.1.0 | - | KaTeX Wrapper |
| eslint | ^9 | - | Linting |

---

## Dependency Graph

```mermaid
graph TD
    subgraph "Production"
        next[next@16.1.2]
        react[react@19.2.3]
        reactdom[react-dom@19.2.3]
        katex[katex@0.16.27]
        reactkatex[react-katex@3.1.0]
    end

    subgraph "Development"
        typescript[typescript@5]
        tailwind[tailwindcss@4]
        eslint[eslint@9]
        eslintconfig[eslint-config-next]
        postcss[@tailwindcss/postcss]
        types[@types/react, @types/node]
    end

    next --> react
    next --> reactdom
    reactkatex --> katex
    reactkatex --> react
    eslintconfig --> eslint
    eslintconfig --> next
    postcss --> tailwind
```

---

## Performance Characteristics

| Technology | Bundle Size | Load Time | Notes |
|------------|-------------|-----------|-------|
| Next.js | ~90KB (core) | Fast (code-split) | Per-page bundles |
| React | ~40KB (gzipped) | Fast | Shared across pages |
| Tailwind | ~10KB (purged) | Fast | Unused CSS removed |
| KaTeX | ~200KB (CSS+JS) | Moderate | Loaded on demand |

---

## Security Considerations

| Concern | Mitigation |
|---------|------------|
| XSS | React escapes by default |
| `dangerouslySetInnerHTML` | Only used for controlled data (tables) |
| Dependencies | Regular `npm audit` |
| Build secrets | None (static data only) |

---

## Future Technology Considerations

| Technology | Purpose | When to Consider |
|------------|---------|------------------|
| Algolia | Server-side search | Index > 10,000 items |
| Elasticsearch | Full-text search | Complex queries needed |
| Prisma + SQLite | Database | Need for dynamic data |
| Vercel Edge | Edge rendering | Global performance |
| MDX | Content authoring | User-contributed content |

---

*이전 문서: [Data Architecture](./04-data-architecture.md)*
*다음 문서: [ADR Index](../adr/README.md)*
