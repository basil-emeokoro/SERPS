"use client";

import Link from "next/link";
import { useEffect, useState } from "react";

export function GlobalPageControls() {
  const [showTop, setShowTop] = useState(false);
  useEffect(() => {
    const update = () => setShowTop(window.scrollY > 520);
    update();
    window.addEventListener("scroll", update, { passive: true });
    return () => window.removeEventListener("scroll", update);
  }, []);
  function returnToTop() {
    const reduced = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    window.scrollTo({ top: 0, behavior: reduced ? "auto" : "smooth" });
  }
  return <>
    {showTop && <button className="return-to-top" type="button" aria-label="Return to top" title="Return to top" onClick={returnToTop}>↑</button>}
    <footer className="site-footer"><div><strong>SERPS POP</strong><span>Secure Explainable Remote Proctoring System</span></div><div><span>Research Prototype Version 1.0 RC1</span><nav aria-label="Footer"><Link href="/#about">Privacy</Link><Link href="/#documentation">Documentation</Link><Link href="/#version">Prototype Limitations</Link></nav></div></footer>
  </>;
}
