export type ProtectionReason = "monitoring_verification" | "connectivity_interrupted" | "policy_review";
export type ProtectionState = { mode: "NORMAL" | "PROTECTED"; reason: ProtectionReason | null; enteredAt: number | null; accumulatedPausedMs: number };

export const normalProtectionState = (): ProtectionState => ({ mode: "NORMAL", reason: null, enteredAt: null, accumulatedPausedMs: 0 });

export function enterProtection(state: ProtectionState, reason: ProtectionReason, now: number): ProtectionState {
  if (state.mode === "PROTECTED") return state.reason === "policy_review" ? state : { ...state, reason };
  return { ...state, mode: "PROTECTED", reason, enteredAt: now };
}

export function clearProtection(state: ProtectionState, now: number, policyRecoveryConfirmed = false): ProtectionState {
  if (state.mode === "NORMAL" || state.enteredAt == null || (state.reason === "policy_review" && !policyRecoveryConfirmed)) return state;
  return { mode: "NORMAL", reason: null, enteredAt: null, accumulatedPausedMs: state.accumulatedPausedMs + Math.max(0, now - state.enteredAt) };
}

export function activeElapsedMs(startedAt: string, now: number, state: ProtectionState): number {
  const timestamp = Date.parse(startedAt.endsWith("Z") || /[+-]\d\d:\d\d$/.test(startedAt) ? startedAt : `${startedAt}Z`);
  const activePause = state.mode === "PROTECTED" && state.enteredAt != null ? Math.max(0, now - state.enteredAt) : 0;
  return Math.max(0, now - timestamp - state.accumulatedPausedMs - activePause);
}

export function interruptionDurationMs(startedAt: number, recoveredAt: number): number { return Math.max(0, recoveredAt - startedAt); }

export function interactionDisabled(state: ProtectionState, monitoringUnavailable: boolean, finished = false): boolean {
  return finished || monitoringUnavailable || state.mode === "PROTECTED";
}

export function monitoringProtectionRequired(phonePolicyArmed: boolean, monitoringUnavailable: boolean): boolean {
  return phonePolicyArmed && monitoringUnavailable;
}

export function canDemoRestore(enabled: boolean, phonePolicyArmed: boolean, reason: ProtectionReason | null): boolean {
  return enabled && phonePolicyArmed && reason === "policy_review";
}

export function formatActiveElapsed(milliseconds: number): string {
  const total = Math.floor(Math.max(0, milliseconds) / 1000);
  const hours = Math.floor(total / 3600).toString().padStart(2, "0");
  const minutes = Math.floor((total % 3600) / 60).toString().padStart(2, "0");
  const seconds = (total % 60).toString().padStart(2, "0");
  return `${hours}:${minutes}:${seconds}`;
}
