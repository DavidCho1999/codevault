"use client";

import { useSearchParams } from "next/navigation";
import { useState, useEffect, Suspense } from "react";
import Link from "next/link";
import { getSnippet } from "@/lib/search";
import type { SearchItem } from "@/lib/types";

function SearchResults() {
  const searchParams = useSearchParams();
  const query = searchParams.get("q") || "";

  const [results, setResults] = useState<SearchItem[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!query.trim()) {
      setResults([]);
      return;
    }

    const fetchResults = async () => {
      setIsLoading(true);
      setError(null);

      try {
        const response = await fetch(`/api/search?q=${encodeURIComponent(query)}`);

        if (!response.ok) {
          throw new Error("검색 중 오류가 발생했습니다");
        }

        const data = await response.json();
        setResults(data.results);
      } catch (err) {
        setError(err instanceof Error ? err.message : "알 수 없는 오류");
        setResults([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchResults();
  }, [query]);

  if (!query) {
    return (
      <div className="text-center py-12 text-gray-500">
        Enter a search term to find code sections
      </div>
    );
  }

  if (isLoading) {
    return (
      <div className="text-center py-12 text-gray-500">
        검색 중...
      </div>
    );
  }

  if (error) {
    return (
      <div className="text-center py-12 text-red-500">
        {error}
      </div>
    );
  }

  return (
    <div>
      <p className="text-sm text-gray-600 mb-6">
        {results.length} result{results.length !== 1 ? "s" : ""} for &quot;{query}&quot;
      </p>

      {results.length === 0 ? (
        <div className="text-center py-12 text-gray-500">
          No results found for &quot;{query}&quot;
        </div>
      ) : (
        <div className="space-y-4">
          {results.map((item) => (
            <Link
              key={item.id}
              href={`/code/${item.id.replace(/\./g, "/")}`}
              className="block p-4 border border-gray-200 rounded-lg hover:border-blue-300 hover:bg-blue-50/30 transition-colors"
            >
              <div className="flex items-start gap-3">
                <span className="font-mono text-sm text-blue-600 font-medium shrink-0">
                  {item.id}
                </span>
                <div className="flex-1 min-w-0">
                  <h3 className="font-medium text-gray-900">{item.title}</h3>
                  <p className="text-sm text-gray-500 mt-0.5">{item.section}</p>
                  {item.content && (
                    <p className="text-sm text-gray-600 mt-2 line-clamp-2">
                      {getSnippet(item.content, query)}
                    </p>
                  )}
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </div>
  );
}

export default function SearchPage() {
  return (
    <div className="p-8 max-w-3xl">
      <h1 className="text-2xl font-bold text-gray-900 mb-6">Search Results</h1>
      <Suspense fallback={<div className="text-gray-500">Loading...</div>}>
        <SearchResults />
      </Suspense>
    </div>
  );
}
