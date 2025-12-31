import type { Metadata } from "next";
import "./globals.css";
import Header from "@/components/layout/Header";

export const metadata: Metadata = {
  title: "News Check | AI-Powered News Summaries",
  description: "Get concise, AI-summarized news from your favorite YouTube channels.",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ja">
      <body>
        <Header />
        <main style={{ paddingTop: '64px', minHeight: '100vh' }}>
          {children}
        </main>
      </body>
    </html>
  );
}
