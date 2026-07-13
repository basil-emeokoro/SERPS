import type { Metadata } from "next";
import "./globals.css";

export const metadata: Metadata = {
  title: "SERPS POP",
  description: "SERPS Production-Oriented Prototype",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  );
}
