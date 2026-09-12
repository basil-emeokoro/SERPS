import { readFileSync } from "node:fs";
import { describe, expect, it } from "vitest";

describe("protected presentation", () => {
  it("defines a fixed, complete viewport shield", () => {
    const css = readFileSync(new URL("../app/globals.css", import.meta.url), "utf8");
    const rule = css.match(/\.examination-protection-overlay\s*\{([^}]+)\}/)?.[1] ?? "";
    expect(rule).toContain("position: fixed");
    expect(rule).toContain("inset: 0");
    expect(rule).toContain("width: 100vw");
    expect(rule).toContain("min-height: 100dvh");
    expect(rule).toContain("z-index: 10000");
  });
});
