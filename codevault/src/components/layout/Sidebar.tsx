"use client";

import { useState } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import type { TocItem } from "@/lib/types";

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
            className="w-5 h-5 flex items-center justify-center text-gray-400 hover:text-gray-600 shrink-0"
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
              ? "bg-blue-50 text-blue-700 font-medium"
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
            <TocNode key={child.id} item={child} depth={depth + 1} />
          ))}
        </div>
      )}
    </div>
  );
}

export default function Sidebar({ toc }: SidebarProps) {
  return (
    <aside className="w-[280px] h-[calc(100vh-56px)] border-r border-gray-200 overflow-y-auto bg-white fixed left-0 top-[56px]">
      <div className="p-3">
        <div className="text-xs font-semibold text-gray-500 uppercase tracking-wider mb-2 px-2">
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
