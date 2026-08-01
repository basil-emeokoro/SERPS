"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";

const links = [
  { label: "Home", href: "/" }, { label: "System Overview", href: "/#system-overview" },
  { label: "Architecture", href: "/#architecture" }, { label: "Candidate Portal", href: "/candidate" },
  { label: "Reviewer Portal", href: "/reviewer" }, { label: "Administrator Portal", href: "/admin" },
  { label: "Documentation", href: "/#documentation" }, { label: "About SERPS", href: "/#about" },
  { label: "Version Information", href: "/#version" },
];

export function AppNavigation() {
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const drawerRef = useRef<HTMLElement>(null);
  function close() { setOpen(false); window.setTimeout(() => triggerRef.current?.focus(), 0); }

  useEffect(() => {
    if (!open) return;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";
    const focusable = () => Array.from(drawerRef.current?.querySelectorAll<HTMLElement>('a[href], button:not([disabled])') ?? []);
    focusable()[0]?.focus();
    function handleKey(event: KeyboardEvent) {
      if (event.key === "Escape") { close(); return; }
      if (event.key !== "Tab") return;
      const items = focusable(); if (!items.length) return;
      const first = items[0]; const last = items[items.length - 1];
      if (event.shiftKey && document.activeElement === first) { event.preventDefault(); last.focus(); }
      else if (!event.shiftKey && document.activeElement === last) { event.preventDefault(); first.focus(); }
    }
    window.addEventListener("keydown", handleKey);
    return () => { document.body.style.overflow = previousOverflow; window.removeEventListener("keydown", handleKey); };
  }, [open]);

  return <>
    <header className="top-bar">
      <Link className="wordmark" href="/" aria-label="SERPS POP home">SERPS POP</Link>
      <button ref={triggerRef} className="menu-button" type="button" aria-expanded={open} aria-controls="serps-navigation-drawer" aria-label={open ? "Close navigation" : "Open navigation"} title={open ? "Close navigation" : "Open navigation"} onClick={() => open ? close() : setOpen(true)}>
        <span className="menu-glyph" aria-hidden="true">{open ? "×" : "☰"}</span>
      </button>
    </header>
    {open && <button className="drawer-backdrop" type="button" aria-label="Close navigation" title="Close navigation" onClick={close} />}
    <aside ref={drawerRef} id="serps-navigation-drawer" className={`navigation-drawer ${open ? "open" : ""}`} aria-hidden={!open} aria-modal="true" role="dialog" aria-label="SERPS navigation">
      <div className="drawer-heading"><div><span>SERPS POP</span><strong>Navigation</strong></div><button type="button" aria-label="Close navigation" title="Close navigation" onClick={close}>×</button></div>
      <nav aria-label="Primary navigation">{links.map((link) => <Link href={link.href} key={link.href} onClick={close}>{link.label}</Link>)}</nav>
      <p>Research Prototype Version 1.0 RC1</p>
    </aside>
  </>;
}
