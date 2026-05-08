import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Market News",
  description:
    "Daily market news aggregator for Taiwan stocks, US stocks, crypto, and macro markets.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen bg-gray-950 text-gray-100 antialiased">
        {children}
      </body>
    </html>
  );
}
