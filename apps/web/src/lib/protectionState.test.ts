import { describe, expect, it } from "vitest";
import { activeElapsedMs, canDemoRestore, clearProtection, enterProtection, formatActiveElapsed, interactionDisabled, interruptionDurationMs, normalProtectionState } from "./protectionState";

describe("examination protection state", () => {
  it("protects, pauses elapsed time, and resumes", () => {
    const start = "2026-09-11T10:00:00Z";
    const protectedState = enterProtection(normalProtectionState(), "monitoring_verification", Date.parse("2026-09-11T10:00:10Z"));
    expect(activeElapsedMs(start, Date.parse("2026-09-11T10:00:30Z"), protectedState)).toBe(10_000);
    const restored = clearProtection(protectedState, Date.parse("2026-09-11T10:00:30Z"));
    expect(restored.mode).toBe("NORMAL");
    expect(activeElapsedMs(start, Date.parse("2026-09-11T10:00:40Z"), restored)).toBe(20_000);
  });
  it("requires governance to clear policy protection", () => {
    const state = enterProtection(normalProtectionState(), "policy_review", 1000);
    expect(clearProtection(state, 5000)).toEqual(state);
    expect(clearProtection(state, 5000, true).mode).toBe("NORMAL");
  });
  it("calculates interruption duration", () => expect(interruptionDurationMs(2000, 7250)).toBe(5250));
  it("formats active elapsed time", () => expect(formatActiveElapsed(3_723_900)).toBe("01:02:03"));
  it("disables controls for protection and monitoring loss", () => {
    expect(interactionDisabled(normalProtectionState(), false)).toBe(false);
    expect(interactionDisabled(normalProtectionState(), true)).toBe(true);
    expect(interactionDisabled(enterProtection(normalProtectionState(), "connectivity_interrupted", 1000), false)).toBe(true);
  });
  it("permits demo recovery only for configured, armed policy protection", () => {
    expect(canDemoRestore(true, true, "policy_review")).toBe(true);
    expect(canDemoRestore(false, true, "policy_review")).toBe(false);
    expect(canDemoRestore(true, false, "policy_review")).toBe(false);
    expect(canDemoRestore(true, true, "monitoring_verification")).toBe(false);
  });
});
