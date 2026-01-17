import type { Metadata } from "next";
import { Geist, Geist_Mono } from "next/font/google";
import "./globals.css";
import Header from "@/components/layout/Header";
import Sidebar from "@/components/layout/Sidebar";
import tocData from "../../public/data/toc.json";

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
  return (
    <html lang="en">
      <body
        className={`${geistSans.variable} ${geistMono.variable} antialiased`}
      >
        <Header />
        <div className="flex pt-[56px]">
          <Sidebar toc={tocData} />
          <main className="flex-1 ml-[280px] min-h-[calc(100vh-56px)] bg-white dark:bg-gray-900">
            {children}
          </main>
        </div>
      </body>
    </html>
  );
}
