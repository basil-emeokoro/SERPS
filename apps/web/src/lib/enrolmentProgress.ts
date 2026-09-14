import type { FaceCapture, LivenessAction } from "./contracts";

export const ENROLMENT_PROGRESS_KEY = "serps_enrolment_progress_v1";

export type EnrolmentProgress = { captures: FaceCapture[]; liveness: LivenessAction[]; actions: string[]; retryCount: number };

export function readEnrolmentProgress(storage: Pick<Storage, "getItem">, poses: string[], actions: string[]): EnrolmentProgress | null {
  try {
    const parsed = JSON.parse(storage.getItem(ENROLMENT_PROGRESS_KEY) ?? "null") as Partial<EnrolmentProgress> | null;
    if (!parsed || !Array.isArray(parsed.captures) || !Array.isArray(parsed.liveness) || !Array.isArray(parsed.actions)) return null;
    const captures = parsed.captures.slice(0, poses.length);
    if (captures.some((capture, index) => capture?.pose !== poses[index])) return null;
    const sameActions = parsed.actions.length === actions.length && parsed.actions.every((action, index) => action === actions[index]);
    return { captures, liveness: sameActions ? parsed.liveness.slice(0, actions.length) : [], actions, retryCount: Number.isInteger(parsed.retryCount) ? Math.max(0, Number(parsed.retryCount)) : 0 };
  } catch { return null; }
}

export function writeEnrolmentProgress(storage: Pick<Storage, "setItem">, progress: EnrolmentProgress): void {
  storage.setItem(ENROLMENT_PROGRESS_KEY, JSON.stringify(progress));
}
