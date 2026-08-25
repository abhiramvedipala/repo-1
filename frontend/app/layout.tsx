import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "Lab Platform",
  description: "Self-hosted interactive coding labs",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="bg-bg text-text antialiased">{children}</body>
    </html>
  );
}
