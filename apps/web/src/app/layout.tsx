import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";

const inter = Inter({ subsets: ["latin"] });

export const metadata: Metadata = {
  title: "VeriDoc - Automated Documentation Pipeline",
  description:
    "Generate, validate, and deploy production-grade API documentation with AI-powered quality gates.",
  icons: {
    icon: "/veridoc-favicon.ico",
    apple: "/veridoc-apple-touch-icon.png",
  },
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className={inter.className}>{children}</body>
    </html>
  );
}
