import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import MainContent from "@/components/layout/MainContent";
import ScrollRestoration from "@/components/layout/ScrollRestoration";
import { ActiveSectionProvider } from "@/lib/ActiveSectionContext";
import { SidebarProvider } from "@/lib/SidebarContext";
import { getToc } from "@/lib/db";

const geistSans = Geist({
  variable: "--font-geist-sans",
  subsets: ["latin"],
});

const geistMono = Geist_Mono({
  variable: "--font-geist-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "CodeVault - Ontario Building Code",
  description: "Search and browse the Ontario Building Code Part 9",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  // DB에서 TOC 조회
  const toc = getToc();

  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <SidebarProvider>
          <ActiveSectionProvider>
            <ScrollRestoration />
            <Header />
            <div className="flex pt-[56px]">
              <Sidebar toc={toc} />
              <MainContent>{children}</MainContent>
            </div>
          </ActiveSectionProvider>
        </SidebarProvider>
      </body>
    </html>
  );
}
