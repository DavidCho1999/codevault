"use client";

import { createContext, useContext, useState, ReactNode } from "react";

interface ActiveSectionContextType {
  activeSection: string | null;
  setActiveSection: (id: string | null) => void;
}

const ActiveSectionContext = createContext<ActiveSectionContextType>({
  activeSection: null,
  setActiveSection: () => {},
});

export function ActiveSectionProvider({ children }: { children: ReactNode }) {
  const [activeSection, setActiveSection] = useState<string | null>(null);

  return (
    <ActiveSectionContext.Provider value={{ activeSection, setActiveSection }}>
      {children}
    </ActiveSectionContext.Provider>
  );
}

export function useActiveSection() {
  return useContext(ActiveSectionContext);
}
