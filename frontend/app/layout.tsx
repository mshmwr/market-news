// MN-005: Root layout — full PWA meta tags + service worker registration.
import type { Metadata } from "next";
import "./globals.css";
import PwaRegister from "@/components/pwa/PwaRegister";

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
        <link rel="manifest" href="/manifest.json" />
        <link rel="apple-touch-icon" href="/icon-192.png" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black" />
        <meta name="apple-mobile-web-app-title" content="市場新聞" />
      </head>
      <body className="antialiased">
        <PwaRegister />
        {children}
      </body>
    </html>
  );
}
