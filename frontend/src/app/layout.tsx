import type { Metadata } from "next";
import Link from "next/link";
import type { ReactNode } from "react";

import "./globals.css";

import { Providers } from "@/app/providers";

export const metadata: Metadata = {
  title: "ChessCoach AI",
  description: "The chess engine that explains the why.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <header className="border-b border-gray-800 bg-gray-900/60 backdrop-blur">
            <div className="mx-auto flex max-w-[1600px] items-center justify-between px-4 py-3 md:px-6">
              <Link href="/" className="text-lg font-bold text-cyan-300">
                ChessCoach AI
              </Link>
              <nav className="flex items-center gap-4 text-sm text-gray-300">
                <Link href="/analyze" className="hover:text-cyan-200">
                  Analyze
                </Link>
                <Link href="/review" className="hover:text-cyan-200">
                  Review
                </Link>
                <Link href="/auth/login" className="hover:text-cyan-200">
                  Login
                </Link>
              </nav>
            </div>
          </header>
          {children}
        </Providers>
      </body>
    </html>
  );
}
