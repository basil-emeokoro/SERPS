import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("protected presentation", () => {
  it("defines a fixed, complete viewport shield", () => {
    const css = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");
    const rule = css.match(/\.examination-protection-overlay\s*\{([^}]+)\}/)?.[1] ?? "";
    expect(rule).toContain("position: fixed");
    expect(rule).toContain("inset: 0");
    expect(rule).toContain("width: 100vw");
    expect(rule).toContain("height: 100dvh");
    expect(rule).toContain("z-index: 10000");
  });

  it("keeps the shield content bounded within the viewport", () => {
    const css = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");
    const panel = css.match(/\.protection-panel\s*\{([^}]+)\}/)?.[1] ?? "";
    expect(panel).toContain("max-height: calc(100dvh - 48px)");
    expect(panel).toContain("overflow: auto");
  });
});
