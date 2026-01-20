"use client";

import { createContext, useContext, useState, ReactNode, useEffect } from "react";

interface SidebarContextType {
  isCollapsed: boolean;
  toggleSidebar: () => void;
}

// Default value for SSR
const defaultContext: SidebarContextType = {
  isCollapsed: false,
  toggleSidebar: () => {},
};

const SidebarContext = createContext<SidebarContextType>(defaultContext);

export function SidebarProvider({ children }: { children: ReactNode }) {
  const [isCollapsed, setIsCollapsed] = useState(false);
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  const toggleSidebar = () => {
    setIsCollapsed((prev) => !prev);
  };

  // SSR 시에도 기본값으로 렌더링
  const value = mounted
    ? { isCollapsed, toggleSidebar }
    : defaultContext;

  return (
    <SidebarContext.Provider value={value}>
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  return useContext(SidebarContext);
}
