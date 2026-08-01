import type { Metadata } from "next";
import { AppNavigation } from "../components/AppNavigation";
import { GlobalPageControls } from "../components/GlobalPageControls";
import "./globals.css";

export const metadata: Metadata = {
  title: "SERPS POP Research Prototype",
  description: "Explainable multi-modal identity assurance, monitoring and governance for external assessment systems.",
};

export default function RootLayout({ children }: Readonly<{ children: React.ReactNode }>) {
  return (
    <html lang="en">
      <body><AppNavigation />{children}<GlobalPageControls /></body>
    </html>
  );
}
