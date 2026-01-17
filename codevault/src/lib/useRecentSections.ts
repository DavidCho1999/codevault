"use client";

import { useState, useEffect, useCallback } from "react";

interface RecentSection {
  id: string;
  title: string;
  visitedAt: number;
}

const STORAGE_KEY = "codevault-recent-sections";
const MAX_ITEMS = 8;

export function useRecentSections() {
  const [recentSections, setRecentSections] = useState<RecentSection[]>([]);

  // localStorage에서 읽기
  useEffect(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored) {
        setRecentSections(JSON.parse(stored));
      }
    } catch (e) {
      console.error("Failed to read recent sections:", e);
    }
  }, []);

  // 섹션 추가
  const addSection = useCallback((id: string, title: string) => {
    setRecentSections((prev) => {
      // 중복 제거
      const filtered = prev.filter((s) => s.id !== id);

      // 새 항목 추가 (맨 앞에)
      const updated = [
        { id, title, visitedAt: Date.now() },
        ...filtered,
      ].slice(0, MAX_ITEMS);

      // localStorage에 저장
      try {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(updated));
      } catch (e) {
        console.error("Failed to save recent sections:", e);
      }

      return updated;
    });
  }, []);

  // 히스토리 초기화
  const clearHistory = useCallback(() => {
    setRecentSections([]);
    try {
      localStorage.removeItem(STORAGE_KEY);
    } catch (e) {
      console.error("Failed to clear recent sections:", e);
    }
  }, []);

  return { recentSections, addSection, clearHistory };
}
