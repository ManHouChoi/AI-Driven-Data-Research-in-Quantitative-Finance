import type { Metadata } from "next";
import "katex/dist/katex.min.css";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "AI-Driven Data Research in Quantitative Finance",
  description:
    "Interactive ST-GAT and NLP risk taxonomy demo for AI-driven quantitative finance research"
};

export default function RootLayout({
  children
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
