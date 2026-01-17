"use client";

import { createContext, useContext } from "react";

interface HighlightContextType {
  highlight: string | null;
}

export const HighlightContext = createContext<HighlightContextType>({
  highlight: null,
});

export function useHighlight() {
  return useContext(HighlightContext);
}

export function HighlightProvider({
  highlight,
  children,
}: {
  highlight: string | null;
  children: React.ReactNode;
}) {
  return (
    <HighlightContext.Provider value={{ highlight }}>
      {children}
    </HighlightContext.Provider>
  );
}
