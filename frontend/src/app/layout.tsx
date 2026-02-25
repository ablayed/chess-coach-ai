import type { Metadata } from "next";
import type { ReactNode } from "react";

import "./globals.css";

import { Providers } from "@/app/providers";
import { SiteHeader } from "@/components/navigation/SiteHeader";

export const metadata: Metadata = {
  title: "ChessCoach AI",
  description: "The chess engine that explains the why.",
};

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <body>
        <Providers>
          <SiteHeader />
          <div className="min-h-[calc(100vh-64px)]">{children}</div>
        </Providers>
      </body>
    </html>
  );
}
