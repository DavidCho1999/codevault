"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { TocItem } from "@/lib/types";
import { useRecentSections } from "@/lib/useRecentSections";
import { useActiveSection } from "@/lib/ActiveSectionContext";
import { useSidebar } from "@/lib/SidebarContext";

interface SidebarProps {
  toc: TocItem[];
}

function TocNode({ item, depth = 0, parentId }: { item: TocItem; depth?: number; parentId?: string }) {
  const pathname = usePathname();
  const { activeSection } = useActiveSection();
  const [isOpen, setIsOpen] = useState(
    pathname?.includes(item.id) || false
  );
  const hasChildren = item.children && item.children.length > 0;

  const isSubsection = depth > 0 && parentId;
  const href = isSubsection
    ? `/code/${parentId}#${item.id}`
    : `/code/${item.id}`;

  const isScrollActive = activeSection === item.id || activeSection?.startsWith(item.id + ".");
  const isUrlActive = pathname === `/code/${item.id}` || (parentId && pathname === `/code/${parentId}`);
  const isActive = isScrollActive || (!activeSection && isUrlActive);

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
            className="w-5 h-5 flex items-center justify-center text-gray-400 hover:text-gray-500 shrink-0"
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
          href={href}
          className={`flex-1 py-1.5 px-2 text-sm rounded-md truncate ${
            isActive
              ? "bg-gray-100 text-gray-900 font-semibold border-l-4 border-gray-900"
              : "text-gray-700 hover:bg-gray-100"
          }`}
          title={`${item.id}. ${item.title}`}
        >
          <span className="font-mono text-xs text-gray-400 mr-1.5">
            {item.id}
          </span>
          {item.title}
        </Link>
      </div>
      {hasChildren && isOpen && (
        <div className="ml-3 border-l border-gray-200 pl-1">
          {item.children.map((child) => (
            <TocNode key={child.id} item={child} depth={depth + 1} parentId={item.id} />
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
    <div className="mb-4 pb-3 border-b border-gray-200">
      <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 px-2 flex items-center gap-1.5">
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
                  ? "bg-gray-100 text-gray-900 font-semibold border-l-4 border-gray-900"
                  : "text-gray-600 hover:bg-gray-100"
              }`}
              title={`${section.id} ${section.title}`}
            >
              <span className="font-mono text-xs text-gray-400 mr-1.5">
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
  const pathname = usePathname();
  const { isCollapsed, toggleSidebar } = useSidebar();

  // Part별로 TOC 분리
  const part2Toc = toc.filter((item) => item.id.startsWith("2."));
  const part7Toc = toc.filter((item) => item.id.startsWith("7."));
  const part8Toc = toc.filter((item) => item.id.startsWith("8."));
  const part9Toc = toc.filter((item) => item.id.startsWith("9."));
  const part10Toc = toc.filter((item) => item.id.startsWith("10."));
  const part11Toc = toc.filter((item) => item.id.startsWith("11."));
  const part12Toc = toc.filter((item) => item.id.startsWith("12."));

  // Part collapse 상태 (현재 보고 있는 Part는 열림)
  const [part2Open, setPart2Open] = useState(pathname?.startsWith("/code/2.") ?? false);
  const [part7Open, setPart7Open] = useState(pathname?.startsWith("/code/7.") ?? false);
  const [part8Open, setPart8Open] = useState(pathname?.startsWith("/code/8.") ?? false);
  const [part9Open, setPart9Open] = useState(pathname?.startsWith("/code/9.") ?? true);
  const [part10Open, setPart10Open] = useState(pathname?.startsWith("/code/10.") ?? false);
  const [part11Open, setPart11Open] = useState(pathname?.startsWith("/code/11.") ?? false);
  const [part12Open, setPart12Open] = useState(pathname?.startsWith("/code/12.") ?? false);

  return (
    <>
      {/* Collapse Toggle Button - 항상 표시 */}
      <button
        onClick={toggleSidebar}
        className={`fixed top-[calc(56px+12px)] z-50 w-6 h-6 flex items-center justify-center bg-white border border-gray-200 rounded-full shadow-sm hover:bg-gray-50 transition-all duration-300 ${
          isCollapsed ? "left-2" : "left-[268px]"
        }`}
        title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
      >
        <svg
          className={`w-3.5 h-3.5 text-gray-500 transition-transform duration-300 ${
            isCollapsed ? "rotate-180" : ""
          }`}
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 19l-7-7 7-7" />
        </svg>
      </button>

      {/* Sidebar */}
      <aside
        className={`h-[calc(100vh-56px)] border-r border-gray-200 overflow-y-auto overscroll-contain bg-white fixed left-0 top-[56px] transition-all duration-300 ${
          isCollapsed ? "w-0 -translate-x-full" : "w-[280px] translate-x-0"
        }`}
      >
        <div className="p-3 w-[280px]">
          <RecentSections />

          {/* Division A Header */}
          <div className="text-[10px] font-bold text-blue-600 uppercase tracking-wider mb-1 px-2 mt-2">
            Division A - Compliance, Objectives and Functional Statements
          </div>

          {/* Part 2 */}
          {part2Toc.length > 0 && (
            <>
              <div className="flex items-center gap-1 mb-2 px-2">
                <button
                  onClick={() => setPart2Open(!part2Open)}
                  className="shrink-0 hover:text-gray-700 transition-colors"
                >
                  <svg
                    className={`w-3 h-3 transition-transform ${part2Open ? "rotate-90" : ""}`}
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
                <Link
                  href="/code/2.1"
                  onClick={() => setPart2Open(true)}
                  className="text-xs font-semibold text-gray-500 uppercase tracking-wider hover:text-gray-700 transition-colors"
                >
                  Part 2 - Objectives
                </Link>
              </div>
              {part2Open && (
                <nav className="mb-4">
                  {part2Toc.map((section) => (
                    <TocNode key={section.id} item={section} />
                  ))}
                </nav>
              )}
            </>
          )}

          {/* Division B Header */}
          <div className="text-[10px] font-bold text-green-600 uppercase tracking-wider mb-1 px-2 mt-4">
            Division B - Acceptable Solutions
          </div>

          {/* Part 7 */}
          {part7Toc.length > 0 && (
            <>
              <div className="flex items-center gap-1 mb-2 px-2">
                <button
                  onClick={() => setPart7Open(!part7Open)}
                  className="shrink-0 hover:text-gray-700 transition-colors"
                >
                  <svg
                    className={`w-3 h-3 transition-transform ${part7Open ? "rotate-90" : ""}`}
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
                <Link
                  href="/code/7"
                  onClick={() => setPart7Open(true)}
                  className="text-xs font-semibold text-gray-500 uppercase tracking-wider hover:text-gray-700 transition-colors"
                >
                  Part 7 - Plumbing
                </Link>
              </div>
              {part7Open && (
                <nav className="mb-4">
                  {part7Toc.map((section) => (
                    <TocNode key={section.id} item={section} />
                  ))}
                </nav>
              )}
            </>
          )}

          {/* Part 8 */}
          {part8Toc.length > 0 && (
            <>
              <div className="flex items-center gap-1 mb-2 px-2">
                <button
                  onClick={() => setPart8Open(!part8Open)}
                  className="shrink-0 hover:text-gray-700 transition-colors"
                >
                  <svg
                    className={`w-3 h-3 transition-transform ${part8Open ? "rotate-90" : ""}`}
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
                <Link
                  href="/code/8"
                  onClick={() => setPart8Open(true)}
                  className="text-xs font-semibold text-gray-500 uppercase tracking-wider hover:text-gray-700 transition-colors"
                >
                  Part 8 - Sewage Systems
                </Link>
              </div>
              {part8Open && (
                <nav className="mb-4">
                  {part8Toc.map((section) => (
                    <TocNode key={section.id} item={section} />
                  ))}
                </nav>
              )}
            </>
          )}

          {/* Part 9 */}
          <div className="flex items-center gap-1 mb-2 px-2">
            <button
              onClick={() => setPart9Open(!part9Open)}
              className="shrink-0 hover:text-gray-700 transition-colors"
            >
              <svg
                className={`w-3 h-3 transition-transform ${part9Open ? "rotate-90" : ""}`}
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
            <Link
              href="/code/9"
              onClick={() => setPart9Open(true)}
              className="text-xs font-semibold text-gray-500 uppercase tracking-wider hover:text-gray-700 transition-colors"
            >
              Part 9 - Housing and Small Buildings
            </Link>
          </div>
          {part9Open && (
            <nav className="mb-4">
              {part9Toc.map((section) => (
                <TocNode key={section.id} item={section} />
              ))}
            </nav>
          )}

          {/* Part 10 */}
          {part10Toc.length > 0 && (
            <>
              <div className="flex items-center gap-1 mb-2 px-2">
                <button
                  onClick={() => setPart10Open(!part10Open)}
                  className="shrink-0 hover:text-gray-700 transition-colors"
                >
                  <svg
                    className={`w-3 h-3 transition-transform ${part10Open ? "rotate-90" : ""}`}
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
                <Link
                  href="/code/10"
                  onClick={() => setPart10Open(true)}
                  className="text-xs font-semibold text-gray-500 uppercase tracking-wider hover:text-gray-700 transition-colors"
                >
                  Part 10 - Change of Use
                </Link>
              </div>
              {part10Open && (
                <nav className="mb-4">
                  {part10Toc.map((section) => (
                    <TocNode key={section.id} item={section} />
                  ))}
                </nav>
              )}
            </>
          )}

          {/* Part 11 */}
          {part11Toc.length > 0 && (
            <>
              <div className="flex items-center gap-1 mb-2 px-2">
                <button
                  onClick={() => setPart11Open(!part11Open)}
                  className="shrink-0 hover:text-gray-700 transition-colors"
                >
                  <svg
                    className={`w-3 h-3 transition-transform ${part11Open ? "rotate-90" : ""}`}
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
                <Link
                  href="/code/11"
                  onClick={() => setPart11Open(true)}
                  className="text-xs font-semibold text-gray-500 uppercase tracking-wider hover:text-gray-700 transition-colors"
                >
                  Part 11 - Renovation
                </Link>
              </div>
              {part11Open && (
                <nav className="mb-4">
                  {part11Toc.map((section) => (
                    <TocNode key={section.id} item={section} />
                  ))}
                </nav>
              )}
            </>
          )}

          {/* Part 12 */}
          {part12Toc.length > 0 && (
            <>
              <div className="flex items-center gap-1 mb-2 px-2">
                <button
                  onClick={() => setPart12Open(!part12Open)}
                  className="shrink-0 hover:text-gray-700 transition-colors"
                >
                  <svg
                    className={`w-3 h-3 transition-transform ${part12Open ? "rotate-90" : ""}`}
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
                <Link
                  href="/code/12"
                  onClick={() => setPart12Open(true)}
                  className="text-xs font-semibold text-gray-500 uppercase tracking-wider hover:text-gray-700 transition-colors"
                >
                  Part 12 - Resource Conservation
                </Link>
              </div>
              {part12Open && (
                <nav className="mb-4">
                  {part12Toc.map((section) => (
                    <TocNode key={section.id} item={section} />
                  ))}
                </nav>
              )}
            </>
          )}
        </div>
      </aside>
    </>
  );
}
