import type { AdministratorMetrics, CandidateWorkspace, InstitutionalPolicy, MeResponse, OperationalSessionDetail, ReviewerQueueItem } from "./contracts";
export type { MeResponse } from "./contracts";
export type ApiHealth = { status: string; service: string; version: string };
export type LoginPayload = { email: string; password: string; institution_code?: string };
export type TokenResponse = { access_token: string; refresh_token: string; token_type: "bearer"; expires_in: number };
export type AssignedExamination = { assignment_id: string; assignment_status: string; examination_id: string; exam_code: string; title: string; status: string; starts_at: string | null; ends_at: string | null; duration_minutes: number; monitoring_mode: string };
export type CandidateDashboard = { candidate: { candidate_id: string; full_name: string; email: string; status: string }; assigned_examinations: AssignedExamination[]; consent: { accepted: boolean; consent_version: string } | null; device_check: { passed: boolean; browser_name: string } | null; primary_camera_selection: { camera_selection_id: string; label: string | null; camera_count: number } | null; primary_camera_permission: { granted: boolean; status: string } | null; secondary_camera_selection: { camera_selection_id: string; label: string | null; camera_count: number } | null; secondary_camera_permission: { granted: boolean; status: string } | null; active_session: { session_id: string; examination_id: string; status: string } | null; readiness: Record<string, boolean> };

export class ApiError extends Error { constructor(message: string, public readonly status: number) { super(message); } }
export class SessionExpiredError extends ApiError {}
export function getApiBaseUrl(): string { return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"; }
export function storedAccessToken(): string { return typeof window === "undefined" ? "" : sessionStorage.getItem("serps_access_token") ?? ""; }
function detailMessage(body: unknown, fallback: string): string {
  if (typeof body === "object" && body !== null && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((item) => typeof item === "object" && item && "msg" in item ? String(item.msg) : String(item)).join("; ");
  }
  return fallback;
}
export async function apiRequest<T>(path: string, options: RequestInit & { token?: string; retry?: boolean } = {}): Promise<T> {
  const { token = storedAccessToken(), retry = false, ...init } = options;
  const execute = () => fetch(`${getApiBaseUrl()}${path}`, { ...init, headers: { ...(init.body ? { "Content-Type": "application/json" } : {}), ...(token ? { Authorization: `Bearer ${token}` } : {}), ...(init.headers ?? {}) }, cache: "no-store" });
  let response: Response;
  try { response = await execute(); } catch (error) { if (!retry || (init.method && init.method !== "GET")) throw error; response = await execute(); }
  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const message = detailMessage(body, `SERPS request failed with ${response.status}.`);
    if (response.status === 401) {
      if (typeof window !== "undefined") ["serps_access_token", "serps_refresh_token", "serps_current_user"].forEach((key) => sessionStorage.removeItem(key));
      throw new SessionExpiredError(message || "Your session expired. Sign in again.", response.status);
    }
    throw new ApiError(message, response.status);
  }
  if (response.status === 204) return undefined as T;
  return response.json() as Promise<T>;
}
export function fetchApiHealth(): Promise<ApiHealth> { return apiRequest("/api/v1/health", { retry: true }); }
export function login(payload: LoginPayload): Promise<TokenResponse> { return apiRequest("/api/v1/auth/login", { method: "POST", token: "", body: JSON.stringify(payload) }); }
export function fetchCurrentUser(accessToken: string, signal?: AbortSignal): Promise<MeResponse> { return apiRequest("/api/v1/auth/me", { token: accessToken, signal }); }
export function registerCandidate(payload: Record<string, string>): Promise<Record<string, string>> { return apiRequest("/api/v1/candidate/register", { method: "POST", token: "", body: JSON.stringify(payload) }); }
export function fetchCandidateDashboard(signal?: AbortSignal): Promise<CandidateDashboard> { return apiRequest("/api/v1/candidate/dashboard", { signal, retry: true }); }
export function acceptCandidateConsent(): Promise<unknown> { return apiRequest("/api/v1/candidate/consents", { method: "POST", body: JSON.stringify({ consent_version: "CONSENT-1.0", monitoring_consent: true, privacy_notice_accepted: true, institutional_policy_accepted: true }) }); }
export function submitDeviceCheck(payload: Record<string, unknown>): Promise<unknown> { return apiRequest("/api/v1/candidate/device-checks", { method: "POST", body: JSON.stringify(payload) }); }
export function submitCameraSelection(payload: Record<string, unknown>): Promise<unknown> { return apiRequest("/api/v1/candidate/cameras", { method: "POST", body: JSON.stringify(payload) }); }
export function submitCameraPermission(cameraRole: "primary" | "secondary", status: string): Promise<unknown> { return apiRequest("/api/v1/candidate/camera-permissions", { method: "POST", body: JSON.stringify({ camera_role: cameraRole, status, user_agent: navigator.userAgent }) }); }
export function startCandidateSession(examinationId: string): Promise<{ session_id: string; candidate_id: string }> { return apiRequest(`/api/v1/candidate/examinations/${examinationId}/start`, { method: "POST", body: JSON.stringify({ deployment_mode: "A" }) }); }
export function fetchCandidateWorkspace(sessionId: string, signal?: AbortSignal): Promise<CandidateWorkspace> { return apiRequest(`/api/v1/candidate/sessions/${sessionId}`, { signal, retry: true }); }
export function completeCandidateSession(sessionId: string): Promise<unknown> { return apiRequest(`/api/v1/candidate/sessions/${sessionId}/complete`, { method: "POST" }); }
export function submitEvidenceEvent(payload: { session_id: string; candidate_id: string; event_type: string; description: string; confidence?: number; camera_id?: "primary" | "secondary" }): Promise<unknown> { return apiRequest("/api/v1/evidence-events/", { method: "POST", body: JSON.stringify({ ...payload, source_module: "candidate_browser", risk_weight: payload.event_type === "camera_disconnected" ? 0.7 : 0.3, confidence: payload.confidence ?? 1.0 }) }); }
export function fetchReviewerQueue(query = "", signal?: AbortSignal): Promise<ReviewerQueueItem[]> { return apiRequest(`/api/v1/reviewer/sessions${query ? `?${query}` : ""}`, { signal, retry: true }); }
export function fetchReviewerSession(sessionId: string, role: "reviewer" | "admin" = "reviewer", signal?: AbortSignal): Promise<OperationalSessionDetail> { return apiRequest(`/api/v1/${role}/sessions/${sessionId}`, { signal, retry: true }); }
export function submitReviewerDecision(sessionId: string, payload: Record<string, unknown>): Promise<unknown> { return apiRequest(`/api/v1/examination-sessions/${sessionId}/reviewer-decisions`, { method: "POST", body: JSON.stringify(payload) }); }
export function generateSessionReport(sessionId: string): Promise<Record<string, unknown>> { return apiRequest(`/api/v1/examination-sessions/${sessionId}/reports`, { method: "POST" }); }
export function fetchGovernanceTimeline(sessionId: string, signal?: AbortSignal): Promise<Record<string, unknown>[]> { return apiRequest(`/api/v1/examination-sessions/${sessionId}/governance-timeline`, { signal, retry: true }); }
export function fetchSessionReport(sessionId: string, reportId: string, signal?: AbortSignal): Promise<Record<string, unknown>> { return apiRequest(`/api/v1/examination-sessions/${sessionId}/reports/${reportId}`, { signal, retry: true }); }
export function fetchAdminMetrics(signal?: AbortSignal): Promise<AdministratorMetrics> { return apiRequest("/api/v1/admin/metrics", { signal, retry: true }); }
export function fetchAdminPolicy(signal?: AbortSignal): Promise<InstitutionalPolicy | null> { return apiRequest("/api/v1/admin/policy", { signal, retry: true }); }
