import type { FaceCapture, LivenessAction } from "./contracts";

export const ENROLMENT_PROGRESS_KEY = "serps_enrolment_progress_v1";

export type EnrolmentProgress = { subject: string; captures: FaceCapture[]; liveness: LivenessAction[]; actions: string[]; retryCount: number };

export function readEnrolmentProgress(storage: Pick<Storage, "getItem">, subject: string, poses: string[], actions: string[]): EnrolmentProgress | null {
  try {
    const parsed = JSON.parse(storage.getItem(ENROLMENT_PROGRESS_KEY) ?? "null") as Partial<EnrolmentProgress> | null;
    if (!parsed || parsed.subject !== subject || !Array.isArray(parsed.captures) || !Array.isArray(parsed.liveness) || !Array.isArray(parsed.actions)) return null;
    const captures = parsed.captures.slice(0, poses.length);
    if (captures.some((capture, index) => capture?.pose !== poses[index])) return null;
    const firstInvalid = captures.findIndex((capture) => capture.lighting_score < 0.45 || capture.distance_score < 0.45 || capture.confidence < 0.55);
    const validCaptures = firstInvalid === -1 ? captures : captures.slice(0, firstInvalid);
    return { subject, captures: validCaptures, liveness: [], actions, retryCount: Number.isInteger(parsed.retryCount) ? Math.max(0, Number(parsed.retryCount)) : 0 };
  } catch { return null; }
}

export function writeEnrolmentProgress(storage: Pick<Storage, "setItem">, progress: EnrolmentProgress): void {
  storage.setItem(ENROLMENT_PROGRESS_KEY, JSON.stringify(progress));
}
