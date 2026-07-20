import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SERPS Operational Early Alpha",
  description: "Explainable multi-modal identity assurance, monitoring and governance for external assessment systems.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
