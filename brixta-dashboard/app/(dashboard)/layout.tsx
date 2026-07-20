// app/layout.tsx

import type { Metadata } from "next";
import "../globals.css";
import { ReactNode } from "react";
import { ThemeProvider } from "@/components/providers/ThemeProvider";
import Sidebar from "@/components/layout/Sidebar";

// This automatically injects the <title> and <meta name="description"> 
// into your HTML head for better SEO and browser tab rendering.
export const metadata: Metadata = {
  title: "BRIXTA Dashboard",
  description: "High-performance vectorization pipeline.",
  icons: {
    icon: "/brixta.ico",
  }
};

export default function RootLayout({
  children,
}: {
  children: ReactNode;
}) {
  return (
    // 'suppressHydrationWarning' is highly recommended if you ever plan 
    // to add a Dark Mode toggle later via next-themes.
    <html lang="en" suppressHydrationWarning>
      {/* antialiased: Makes fonts render much sharper
        min-h-screen: Ensures the body always fills the monitor 
        bg-background text-foreground: Hooks into your Tailwind/shadcn color variables
      */}
      <body
        suppressHydrationWarning
        className="min-h-screen bg-background text-foreground antialiased"
      >
        <ThemeProvider>
          {/* This grid/flex wrapper is what creates the sidebar layout */}
          <div className="flex min-h-screen w-full bg-background">
            <Sidebar />
            <main className="flex-1 overflow-y-auto">
              {children}
            </main>
          </div>
        </ThemeProvider>
      </body>
    </html>
  );
}
