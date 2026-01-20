"use client";

import { useEffect, useRef } from "react";
import { usePathname } from "next/navigation";

/**
 * 전역 스크롤 복원 컴포넌트
 * - 새로고침 시 스크롤 위치 유지 (sessionStorage)
 * - Hash 기반 스크롤 (새로고침 시에도 작동)
 * - 페이지 변경 시 스크롤 위치 복원
 */
export default function ScrollRestoration() {
  const pathname = usePathname();
  const isRestoringRef = useRef(false);

  // 스크롤 위치 저장 (페이지 이탈 시)
  useEffect(() => {
    const saveScrollPosition = () => {
      const scrollKey = `scroll-${pathname}`;
      sessionStorage.setItem(scrollKey, window.scrollY.toString());
    };

    // 스크롤 이벤트 디바운스
    let scrollTimeout: NodeJS.Timeout;
    const handleScroll = () => {
      clearTimeout(scrollTimeout);
      scrollTimeout = setTimeout(saveScrollPosition, 100);
    };

    window.addEventListener("scroll", handleScroll, { passive: true });
    window.addEventListener("beforeunload", saveScrollPosition);

    return () => {
      clearTimeout(scrollTimeout);
      window.removeEventListener("scroll", handleScroll);
      window.removeEventListener("beforeunload", saveScrollPosition);
    };
  }, [pathname]);

  // 스크롤 위치 복원 (페이지 로드/이동 시)
  useEffect(() => {
    const hash = window.location.hash.slice(1); // # 제거

    if (hash) {
      // Hash 우선: 요소로 스크롤
      let attempts = 0;
      const maxAttempts = 10; // 최대 3초 대기 (300ms * 10)

      const scrollToHash = () => {
        const element = document.getElementById(hash);

        if (element) {
          isRestoringRef.current = true;
          element.scrollIntoView({ behavior: "smooth", block: "start" });
          setTimeout(() => {
            isRestoringRef.current = false;
          }, 1000);
        } else if (attempts < maxAttempts) {
          attempts++;
          setTimeout(scrollToHash, 300);
        }
      };

      setTimeout(scrollToHash, 100);
    } else {
      // Hash 없으면 저장된 스크롤 위치 복원
      const scrollKey = `scroll-${pathname}`;
      const savedPosition = sessionStorage.getItem(scrollKey);

      if (savedPosition) {
        const scrollY = parseInt(savedPosition, 10);

        // 복원 시도
        const restore = () => {
          if (document.body.scrollHeight > scrollY) {
            isRestoringRef.current = true;
            window.scrollTo({ top: scrollY, behavior: "instant" });
            setTimeout(() => {
              isRestoringRef.current = false;
            }, 500);
          } else {
            // 페이지 높이가 부족하면 100ms 후 재시도
            setTimeout(restore, 100);
          }
        };

        // 초기 대기
        setTimeout(restore, 50);
      }
    }
  }, [pathname]);

  // Hashchange 이벤트 리스너 (같은 페이지에서 hash만 변경될 때)
  useEffect(() => {
    const handleHashChange = () => {
      const hash = window.location.hash.slice(1);
      if (hash) {
        const element = document.getElementById(hash);
        if (element) {
          element.scrollIntoView({ behavior: "smooth", block: "start" });
        }
      }
    };

    window.addEventListener("hashchange", handleHashChange);
    return () => window.removeEventListener("hashchange", handleHashChange);
  }, []);

  return null; // UI 없음
}
