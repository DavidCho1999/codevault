"use client";

import ReactMarkdown from "react-markdown";
import remarkMath from "remark-math";
import remarkGfm from "remark-gfm";
import rehypeKatex from "rehype-katex";
import rehypeRaw from "rehype-raw";
import "katex/dist/katex.min.css";
import { useEffect, useState } from "react";

interface Article {
  id: string;
  title: string;
  content: string;
}

interface Subsection {
  id: string;
  title: string;
  content: string;
  articles: Article[];
}

interface Section {
  id: string;
  title: string;
  subsections: Subsection[];
}

interface Part10Data {
  id: string;
  title: string;
  sections: Section[];
}

export default function Part10TestPage() {
  const [data, setData] = useState<Part10Data | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch("/data/part10.json")
      .then((res) => res.json())
      .then((json) => {
        setData(json);
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, []);

  if (loading) {
    return (
      <div className="p-8">
        <p>Loading Part 10...</p>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="p-8">
        <p className="text-red-500">Failed to load Part 10 data</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <header className="mb-8 pb-4 border-b-2 border-gray-300">
          <h1 className="text-3xl font-bold text-gray-900">
            Part {data.id}: {data.title}
          </h1>
          <p className="text-gray-600 mt-2">
            Marker PDF 추출 결과 - 마크다운 렌더링 테스트
          </p>
        </header>

        {/* Table of Contents */}
        <nav className="mb-8 p-4 bg-gray-50 rounded-lg">
          <h2 className="font-bold mb-2 text-gray-900">목차</h2>
          <ul className="space-y-1 text-sm">
            {data.sections.map((section) => (
              <li key={section.id}>
                <a href={`#section-${section.id}`} className="text-gray-900 font-medium underline decoration-2 hover:text-gray-700">
                  Section {section.id}: {section.title}
                </a>
                <ul className="ml-4 mt-1 space-y-1">
                  {section.subsections.map((sub) => (
                    <li key={sub.id}>
                      <a href={`#sub-${sub.id}`} className="text-gray-600 hover:underline">
                        {sub.id} {sub.title}
                      </a>
                    </li>
                  ))}
                </ul>
              </li>
            ))}
          </ul>
        </nav>

        {/* Content */}
        {data.sections.map((section) => (
          <section key={section.id} id={`section-${section.id}`} className="mb-12">
            <h2 className="text-2xl font-bold text-gray-900 mb-4 pb-2 border-b-2 border-gray-300">
              Section {section.id}. {section.title}
            </h2>

            {section.subsections.map((sub) => (
              <div key={sub.id} id={`sub-${sub.id}`} className="mb-8 ml-4">
                <h3 className="text-xl font-semibold text-gray-800 mb-3">
                  {sub.id}. {sub.title}
                </h3>

                {sub.content && (
                  <div className="prose prose-gray max-w-none mb-4">
                    <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeRaw, rehypeKatex]}>
                      {sub.content}
                    </ReactMarkdown>
                  </div>
                )}

                {sub.articles.map((article) => (
                  <div key={article.id} id={`art-${article.id}`} className="mb-6 ml-4 p-4 bg-gray-50 rounded-lg">
                    <h4 className="text-lg font-medium text-gray-700 mb-2">
                      <span className="font-mono text-gray-900 font-semibold">{article.id}.</span> {article.title}
                    </h4>
                    <div className="prose prose-sm prose-gray max-w-none prose-p:my-2 prose-li:my-1">
                      <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeRaw, rehypeKatex]}>
                        {article.content}
                      </ReactMarkdown>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </section>
        ))}

        {/* Stats */}
        <footer className="mt-12 pt-4 border-t text-sm text-gray-500">
          <p>Total Sections: {data.sections.length}</p>
          <p>Total Subsections: {data.sections.reduce((acc, s) => acc + s.subsections.length, 0)}</p>
          <p>Total Articles: {data.sections.reduce((acc, s) => acc + s.subsections.reduce((a, sub) => a + sub.articles.length, 0), 0)}</p>
        </footer>
      </div>
    </div>
  );
}
