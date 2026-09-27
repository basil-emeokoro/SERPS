import { describe, expect, it } from "vitest";
import { activeElapsedMs, canDemoRestore, clearProtection, enterProtection, formatActiveElapsed, interactionDisabled, interruptionDurationMs, monitoringProtectionRequired, normalProtectionState } from "./protectionState";

describe("examination protection state", () => {
  it("does not require monitoring protection while the demonstration policy is disarmed", () => {
    expect(monitoringProtectionRequired(false, true)).toBe(false);
    expect(monitoringProtectionRequired(true, true)).toBe(true);
    expect(monitoringProtectionRequired(true, false)).toBe(false);
  });

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

 describe("independent recovery causes", () => {
  it("clears only connectivity and keeps a policy pause and its timer intact", () => {
    let state = enterProtection(normalProtectionState(), "connectivity_interrupted", 1000);
    state = enterProtection(state, "policy_review", 2000);
    state = clearProtection(state, 3000, false, "connectivity_interrupted");
    expect(state.reasons).toEqual(["policy_review"]); expect(state.mode).toBe("PROTECTED");
    expect(state.enteredAt).toBe(1000); expect(state.accumulatedPausedMs).toBe(0);
    state = clearProtection(state, 5000, true, "policy_review");
    expect(state.mode).toBe("NORMAL"); expect(state.accumulatedPausedMs).toBe(4000);
  });
  it("preserves connectivity and monitoring causes when policy recovery occurs first", () => {
    let state = enterProtection(normalProtectionState(), "policy_review", 1000);
    state = enterProtection(state, "connectivity_interrupted", 2000);
    state = enterProtection(state, "monitoring_verification", 2500);
    state = clearProtection(state, 3000, true, "policy_review");
    expect(state.reasons).toEqual(["connectivity_interrupted", "monitoring_verification"]);
    state = clearProtection(state, 4000, false, "connectivity_interrupted");
    expect(state.reason).toBe("monitoring_verification"); expect(state.mode).toBe("PROTECTED");
  });
  it("deduplicates repeated cause entry and recovery across multiple outages", () => {
    let state = normalProtectionState();
    for (const time of [1000, 5000]) {
      state = enterProtection(state, "connectivity_interrupted", time);
      expect(enterProtection(state, "connectivity_interrupted", time + 1)).toBe(state);
      state = clearProtection(state, time + 1000, false, "connectivity_interrupted");
      expect(clearProtection(state, time + 2000, false, "connectivity_interrupted")).toBe(state);
    }
    expect(state.mode).toBe("NORMAL"); expect(state.accumulatedPausedMs).toBe(2000);
  });
});
