"use client";

import { useSidebar } from "@/lib/SidebarContext";

interface MainContentProps {
  children: React.ReactNode;
}

export default function MainContent({ children }: MainContentProps) {
  const { isCollapsed } = useSidebar();

  return (
    <main
      className={`flex-1 min-h-[calc(100vh-56px)] bg-white transition-all duration-300 ${
        isCollapsed ? "ml-0" : "ml-[280px]"
      }`}
    >
      {children}
    </main>
  );
}
