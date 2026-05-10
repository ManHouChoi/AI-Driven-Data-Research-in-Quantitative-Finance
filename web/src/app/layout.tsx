import type { Metadata } from "next";
import "katex/dist/katex.min.css";
import "@/styles/globals.css";

export const metadata: Metadata = {
  title: "Quant Finance Research Demo",
  description: "Interactive ST-GAT and NLP risk taxonomy research demo"
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
