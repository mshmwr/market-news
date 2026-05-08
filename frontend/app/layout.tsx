// MN-004: Root layout — adds theme-color meta (BQ-004-03 minimal PWA signal).
import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "每日市場新聞",
  description:
    "Daily market news aggregator for Taiwan stocks, US stocks, crypto, and macro markets.",
  other: {
    "theme-color": "#1d1d1f",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="zh-Hant">
      <head>
        <meta name="theme-color" content="#1d1d1f" />
      </head>
      <body className="antialiased">
        {children}
      </body>
    </html>
  );
}
