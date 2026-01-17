"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { TocItem } from "@/lib/types";
import { useRecentSections } from "@/lib/useRecentSections";

interface SidebarProps {
  toc: TocItem[];
}

function TocNode({ item, depth = 0 }: { item: TocItem; depth?: number }) {
  const pathname = usePathname();
  const [isOpen, setIsOpen] = useState(
    pathname?.includes(item.id) || depth === 0
  );
  const hasChildren = item.children && item.children.length > 0;
  const isActive = pathname === `/code/${item.id}`;

  return (
    <div>
      <div
        className={`flex items-center group ${
          depth === 0 ? "mt-1" : ""
        }`}
      >
        {hasChildren ? (
          <button
            onClick={() => setIsOpen(!isOpen)}
            className="w-5 h-5 flex items-center justify-center text-gray-400 hover:text-gray-500 dark:text-gray-500 dark:hover:text-gray-400 shrink-0"
          >
            <svg
              className={`w-3 h-3 transition-transform ${
                isOpen ? "rotate-90" : ""
              }`}
              fill="currentColor"
              viewBox="0 0 20 20"
            >
              <path
                fillRule="evenodd"
                d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z"
                clipRule="evenodd"
              />
            </svg>
          </button>
        ) : (
          <span className="w-5 shrink-0" />
        )}
        <Link
          href={`/code/${item.id}`}
          className={`flex-1 py-1.5 px-2 text-sm rounded-md truncate ${
            isActive
              ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 font-medium"
              : "text-gray-700 dark:text-gray-300 hover:bg-gray-100 dark:hover:bg-gray-800"
          }`}
          title={`${item.id}. ${item.title}`}
        >
          <span className="font-mono text-xs text-gray-400 dark:text-gray-500 mr-1.5">
            {item.id}
          </span>
          {item.title}
        </Link>
      </div>
      {hasChildren && isOpen && (
        <div className="ml-3 border-l border-gray-200 dark:border-gray-700 pl-1">
          {item.children.map((child) => (
            <TocNode key={child.id} item={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

function RecentSections() {
  const pathname = usePathname();
  const { recentSections } = useRecentSections();

  if (recentSections.length === 0) return null;

  return (
    <div className="mb-4 pb-3 border-b border-gray-200 dark:border-gray-700">
      <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2 px-2 flex items-center gap-1.5">
        <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        Recent
      </div>
      <div className="space-y-0.5">
        {recentSections.slice(0, 5).map((section) => {
          const isActive = pathname === `/code/${section.id}`;
          return (
            <Link
              key={section.id}
              href={`/code/${section.id}`}
              className={`block py-1.5 px-2 text-sm rounded-md truncate ${
                isActive
                  ? "bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-400 font-medium"
                  : "text-gray-600 dark:text-gray-400 hover:bg-gray-100 dark:hover:bg-gray-800"
              }`}
              title={`${section.id} ${section.title}`}
            >
              <span className="font-mono text-xs text-gray-400 dark:text-gray-500 mr-1.5">
                {section.id}
              </span>
              {section.title}
            </Link>
          );
        })}
      </div>
    </div>
  );
}

export default function Sidebar({ toc }: SidebarProps) {
  return (
    <aside className="w-[280px] h-[calc(100vh-56px)] border-r border-gray-200 dark:border-gray-700 overflow-y-auto bg-white dark:bg-gray-900 fixed left-0 top-[56px]">
      <div className="p-3">
        <RecentSections />
        <div className="text-xs font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-2 px-2">
          Part 9 - Housing and Small Buildings
        </div>
        <nav>
          {toc.map((section) => (
            <TocNode key={section.id} item={section} />
          ))}
        </nav>
      </div>
    </aside>
  );
}
