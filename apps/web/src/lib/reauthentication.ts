import { apiRequest } from "./api";

export type ReauthenticationState = {
  session_id: string; state: "not_required" | "required" | "pending" | "expired" | "failed" | "manual_review" | "completed" | "released";
  required: boolean; requirement_id?: string; challenge_token?: string; conditions?: string[];
  policy_evaluation_id?: string; assessment_id?: string; recommendation_id?: string;
  retry_after?: string | null; attempts?: number; maximum_attempts?: number;
  outcome?: string; identity_confidence?: number | null; return_path?: string;
};
const path = (sessionId: string) => `/api/v1/identity-assurance/reauthentication/sessions/${encodeURIComponent(sessionId)}`;
export const fetchReauthentication = (sessionId: string, signal?: AbortSignal): Promise<ReauthenticationState> => apiRequest(path(sessionId), { signal });
export const beginReauthentication = (sessionId: string): Promise<ReauthenticationState> => apiRequest(`${path(sessionId)}/challenge`, { method: "POST" });
export const verifyReauthentication = (sessionId: string, payload: { challenge_token: string; descriptor: number[]; one_face: boolean; lighting_score: number; distance_score: number; retry_count: number }): Promise<ReauthenticationState> => apiRequest(`${path(sessionId)}/verify`, { method: "POST", body: JSON.stringify(payload) });
export function reauthenticationMessage(state: ReauthenticationState): string {
  if (state.state === "manual_review") return "Identity assurance requires human review. Return to the examination; your session remains active. A reviewer can authorise continuation or a new bounded check. This is not a misconduct determination.";
  if (state.state === "failed") return "This observation did not establish identity assurance. Request a fresh attempt after the retry cooldown; the previous challenge will not be resubmitted.";
  if (state.state === "expired") return "The challenge expired. Request a fresh bounded attempt.";
  if (state.state === "released") return "Continuation authorised by a reviewer; no biometric verification is claimed.";
  if (state.state === "completed") return "Identity verified. Continue in the same examination session.";
  if (state.state === "not_required") return "No identity re-verification is currently required.";
  return "Institutional policy requires a bounded identity check following identity-relevant context.";
}
export function safeExaminationReturn(path: string | null): string {
  return path && /^\/candidate\/examinations\/[A-Za-z0-9-]+$/.test(path) ? path : "/candidate";
}
export function canRequestAttempt(state: ReauthenticationState, now = Date.now()): boolean {
  return state.required && state.state !== "manual_review" && (!state.retry_after || Date.parse(state.retry_after) <= now);
}

export async function attachExaminationPreview(video: HTMLVideoElement, monitoringStream: MediaStream | null | undefined): Promise<MediaStream | null> {
  if (!monitoringStream?.active) return null;
  const preview = monitoringStream.clone();
  video.srcObject = preview;
  try { await video.play(); }
  catch (error) { preview.getTracks().forEach((track) => track.stop()); video.srcObject = null; throw error; }
  return preview;
}
