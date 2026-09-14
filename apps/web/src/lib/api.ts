import type { AdministratorMetrics, CandidateWorkspace, FaceCapture, InstitutionalPolicy, InstitutionRegistration, LivenessAction, MeResponse, OperationalSessionDetail, RegistrationRequest, ReviewerQueueItem } from "./contracts";
export type { MeResponse } from "./contracts";
export type ApiHealth = { status: string; service: string; version: string };
export type LoginPayload = { email: string; password: string; institution_code?: string };
export type TokenResponse = { authentication_stage: "complete"; access_token: string; refresh_token: string; token_type: "bearer"; expires_in: number };
export type FacialStageResponse = { authentication_stage: "facial_required"; challenge_id: string; challenge_token: string; required_actions: string[]; expires_at: string };
export type EnrollmentStageResponse = { authentication_stage: "enrollment_required"; challenge_id: string; challenge_token: string; required_actions: string[]; expires_at: string; capture_restart_required: true };
export type LoginResponse = TokenResponse | FacialStageResponse | EnrollmentStageResponse;
export type AssignedExamination = { assignment_id: string; assignment_status: string; examination_id: string; exam_code: string; title: string; status: string; starts_at: string | null; ends_at: string | null; duration_minutes: number; monitoring_mode: string };
export type CandidateDashboard = { candidate: { candidate_id: string; full_name: string; email: string; status: string }; assigned_examinations: AssignedExamination[]; consent: { accepted: boolean; consent_version: string } | null; device_check: { passed: boolean; browser_name: string } | null; primary_camera_selection: { camera_selection_id: string; label: string | null; camera_count: number } | null; primary_camera_permission: { granted: boolean; status: string } | null; secondary_camera_selection: { camera_selection_id: string; label: string | null; camera_count: number } | null; secondary_camera_permission: { granted: boolean; status: string } | null; active_session: { session_id: string; examination_id: string; status: string } | null; readiness: Record<string, boolean>; readiness_by_mode: Record<"A" | "B" | "C", Record<string, boolean>> };

export class ApiError extends Error { constructor(message: string, public readonly status: number) { super(message); } }
export class SessionExpiredError extends ApiError {}
export function getApiBaseUrl(): string { return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000"; }
export function storedAccessToken(): string { return typeof window === "undefined" ? "" : sessionStorage.getItem("serps_access_token") ?? ""; }
let refreshInFlight: Promise<string> | null = null;

async function refreshAccessToken(): Promise<string> {
  if (typeof window === "undefined") throw new SessionExpiredError("Your session expired. Sign in again.", 401);
  if (refreshInFlight) return refreshInFlight;
  const refreshToken = sessionStorage.getItem("serps_refresh_token");
  if (!refreshToken) throw new SessionExpiredError("Your session expired. Sign in again.", 401);
  refreshInFlight = fetch(`${getApiBaseUrl()}/api/v1/auth/refresh`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ refresh_token: refreshToken }),
    cache: "no-store",
  }).then(async (response) => {
    if (!response.ok) throw new SessionExpiredError("Your session expired. Sign in again.", response.status);
    const tokens = await response.json() as TokenResponse;
    sessionStorage.setItem("serps_access_token", tokens.access_token);
    sessionStorage.setItem("serps_refresh_token", tokens.refresh_token);
    return tokens.access_token;
  }).finally(() => { refreshInFlight = null; });
  return refreshInFlight;
}
function detailMessage(body: unknown, fallback: string): string {
  if (typeof body === "object" && body !== null && "detail" in body) {
    const detail = (body as { detail: unknown }).detail;
    if (typeof detail === "string") return detail;
    if (Array.isArray(detail)) return detail.map((item) => typeof item === "object" && item && "msg" in item ? String(item.msg) : String(item)).join("; ");
  }
  return fallback;
}
export async function apiRequest<T>(path: string, options: RequestInit & { token?: string; retry?: boolean } = {}): Promise<T> {
  const hasExplicitToken = Object.prototype.hasOwnProperty.call(options, "token");
  const { token = storedAccessToken(), retry = false, ...init } = options;
  const execute = (requestToken = token) => fetch(`${getApiBaseUrl()}${path}`, { ...init, headers: { ...(init.body ? { "Content-Type": "application/json" } : {}), ...(requestToken ? { Authorization: `Bearer ${requestToken}` } : {}), ...(init.headers ?? {}) }, cache: "no-store" });
  let response: Response;
  try { response = await execute(); } catch (error) { if (!retry || (init.method && init.method !== "GET")) throw error; response = await execute(); }
  if (response.status === 401 && !hasExplicitToken) {
    try { response = await execute(await refreshAccessToken()); }
    catch (error) {
      if (typeof window !== "undefined") ["serps_access_token", "serps_refresh_token", "serps_current_user"].forEach((key) => sessionStorage.removeItem(key));
      throw error;
    }
  }
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
export function login(payload: LoginPayload): Promise<LoginResponse> { return apiRequest("/api/v1/auth/login", { method: "POST", token: "", body: JSON.stringify(payload) }); }
export function fetchCurrentUser(accessToken?: string, signal?: AbortSignal): Promise<MeResponse> {
  return accessToken
    ? apiRequest("/api/v1/auth/me", { token: accessToken, signal })
    : apiRequest("/api/v1/auth/me", { signal });
}
export function registerCandidate(payload: Record<string, string>): Promise<Record<string, string>> { return apiRequest("/api/v1/candidate/register", { method: "POST", token: "", body: JSON.stringify(payload) }); }
export function registerIdentity(payload: Record<string, unknown>): Promise<RegistrationRequest> { return apiRequest("/api/v1/identity-assurance/registrations", { method: "POST", token: "", body: JSON.stringify(payload) }); }
export function fetchRegistrationInstitutions(signal?: AbortSignal): Promise<InstitutionRegistration[]> { return apiRequest("/api/v1/identity-assurance/institutions", { token: "", signal, retry: true }); }
export function submitEnrollment(payload: { enrollment_token: string; captures: FaceCapture[]; liveness_actions: LivenessAction[]; retry_count: number }): Promise<Record<string, unknown>> { return apiRequest("/api/v1/identity-assurance/enrollments", { method: "POST", token: "", body: JSON.stringify(payload) }); }
export function resumeEnrollment(payload: { institution_code?: string; email: string; password: string }): Promise<{ challenge_token: string; required_actions: string[] }> { return apiRequest("/api/v1/identity-assurance/enrollments/resume", { method: "POST", token: "", body: JSON.stringify(payload) }); }
export function submitFacialAuthentication(payload: { challenge_token: string; descriptor: number[]; one_face: boolean; lighting_score: number; distance_score: number; liveness_actions: LivenessAction[]; retry_count: number }): Promise<Record<string, unknown>> { return apiRequest("/api/v1/identity-assurance/facial-authentication", { method: "POST", token: "", body: JSON.stringify(payload) }); }
export function fetchRegistrations(signal?: AbortSignal): Promise<RegistrationRequest[]> { return apiRequest("/api/v1/identity-assurance/registrations", { signal, retry: true }); }
export function decideRegistration(registrationId: string, decision: "approve" | "reject", rationale: string): Promise<RegistrationRequest> { return apiRequest(`/api/v1/identity-assurance/registrations/${registrationId}/decision`, { method: "POST", body: JSON.stringify({ decision, rationale }) }); }
export function beginPeriodicVerification(): Promise<{ challenge_token: string; required_actions: string[] }> { return apiRequest("/api/v1/identity-assurance/periodic/challenge", { method: "POST" }); }
export function submitPeriodicVerification(payload: { challenge_token: string; descriptor: number[]; one_face: boolean; lighting_score: number; distance_score: number; liveness_actions: LivenessAction[]; retry_count: number }): Promise<Record<string, unknown>> { return apiRequest("/api/v1/identity-assurance/periodic/verify", { method: "POST", body: JSON.stringify(payload) }); }
export function fetchIdentityStatus(): Promise<{ biometric_required: boolean; demo_bypass: boolean; enrolment_status: string; authentication_result: string; identity_confidence: number | null; liveness_result: string; last_verified_at: string | null }> { return apiRequest("/api/v1/identity-assurance/status", { retry: true }); }
export function fetchCandidateDashboard(signal?: AbortSignal): Promise<CandidateDashboard> { return apiRequest("/api/v1/candidate/dashboard", { signal, retry: true }); }
export function acceptCandidateConsent(): Promise<unknown> { return apiRequest("/api/v1/candidate/consents", { method: "POST", body: JSON.stringify({ consent_version: "CONSENT-1.0", monitoring_consent: true, privacy_notice_accepted: true, institutional_policy_accepted: true }) }); }
export function submitDeviceCheck(payload: Record<string, unknown>): Promise<unknown> { return apiRequest("/api/v1/candidate/device-checks", { method: "POST", body: JSON.stringify(payload) }); }
export function submitCameraSelection(payload: Record<string, unknown>): Promise<unknown> { return apiRequest("/api/v1/candidate/cameras", { method: "POST", body: JSON.stringify(payload) }); }
export function submitCameraPermission(cameraRole: "primary" | "secondary", status: string): Promise<unknown> { return apiRequest("/api/v1/candidate/camera-permissions", { method: "POST", body: JSON.stringify({ camera_role: cameraRole, status, user_agent: navigator.userAgent }) }); }
export function startCandidateSession(examinationId: string, deploymentMode: "A" | "B" | "C" = "B"): Promise<{ session_id: string; candidate_id: string }> { return apiRequest(`/api/v1/candidate/examinations/${examinationId}/start`, { method: "POST", body: JSON.stringify({ deployment_mode: deploymentMode }) }); }
export function fetchCandidateWorkspace(sessionId: string, signal?: AbortSignal): Promise<CandidateWorkspace> { return apiRequest(`/api/v1/candidate/sessions/${sessionId}`, { signal, retry: true }); }
export type CandidateProtection = { state: "NORMAL" | "PROTECTED"; reason_category: string | null; policy_action: string | null; requires_reviewer: boolean; misconduct_determination: boolean; evaluated_at: string | null; demo_controls_enabled: boolean; demo_phone_policy_armed: boolean };
export function fetchCandidateProtection(sessionId: string, signal?: AbortSignal): Promise<CandidateProtection> { return apiRequest(`/api/v1/candidate/sessions/${sessionId}/protection`, { signal }); }
export function updateDemoPhonePolicy(sessionId: string, armed: boolean): Promise<CandidateProtection> { return apiRequest(`/api/v1/candidate/sessions/${sessionId}/demo-phone-policy`, { method: "POST", body: JSON.stringify({ armed }) }); }
export function completeCandidateSession(sessionId: string): Promise<unknown> { return apiRequest(`/api/v1/candidate/sessions/${sessionId}/complete`, { method: "POST" }); }
export function submitEvidenceEvent(payload: { session_id: string; candidate_id: string; event_type: string; description: string; confidence?: number; camera_id?: "primary" | "secondary"; risk_weight?: number; metadata_json?: Record<string, unknown> }): Promise<unknown> { return apiRequest("/api/v1/evidence-events/", { method: "POST", body: JSON.stringify({ ...payload, source_module: "candidate_browser", risk_weight: payload.risk_weight ?? (payload.event_type === "camera_disconnected" ? 0.7 : 0.3), confidence: payload.confidence ?? 1.0 }) }); }
export function fetchReviewerQueue(query = "", signal?: AbortSignal): Promise<ReviewerQueueItem[]> { return apiRequest(`/api/v1/reviewer/sessions${query ? `?${query}` : ""}`, { signal, retry: true }); }
export function fetchReviewerSession(sessionId: string, role: "reviewer" | "admin" = "reviewer", signal?: AbortSignal): Promise<OperationalSessionDetail> { return apiRequest(`/api/v1/${role}/sessions/${sessionId}`, { signal, retry: true }); }
export function submitReviewerDecision(sessionId: string, payload: Record<string, unknown>): Promise<unknown> { return apiRequest(`/api/v1/examination-sessions/${sessionId}/reviewer-decisions`, { method: "POST", body: JSON.stringify(payload) }); }
export function generateSessionReport(sessionId: string): Promise<Record<string, unknown>> { return apiRequest(`/api/v1/examination-sessions/${sessionId}/reports`, { method: "POST" }); }
export function fetchGovernanceTimeline(sessionId: string, signal?: AbortSignal): Promise<Record<string, unknown>[]> { return apiRequest(`/api/v1/examination-sessions/${sessionId}/governance-timeline`, { signal, retry: true }); }
export function fetchSessionReport(sessionId: string, reportId: string, signal?: AbortSignal): Promise<Record<string, unknown>> { return apiRequest(`/api/v1/examination-sessions/${sessionId}/reports/${reportId}`, { signal, retry: true }); }
export function fetchAdminMetrics(signal?: AbortSignal): Promise<AdministratorMetrics> { return apiRequest("/api/v1/admin/metrics", { signal, retry: true }); }
export function fetchAdminPolicy(signal?: AbortSignal): Promise<InstitutionalPolicy | null> { return apiRequest("/api/v1/admin/policy", { signal, retry: true }); }
