export type ApiHealth = {
  status: string;
  service: string;
  version: string;
};

export type LoginPayload = {
  email: string;
  password: string;
  institution_code?: string;
};

export type TokenResponse = {
  access_token: string;
  refresh_token: string;
  token_type: "bearer";
  expires_in: number;
};

export type MeResponse = {
  user_id: string;
  institution_id: string;
  email: string;
  full_name: string;
  roles: string[];
};

export type AssignedExamination = {
  assignment_id: string;
  assignment_status: string;
  examination_id: string;
  exam_code: string;
  title: string;
  status: string;
  starts_at: string | null;
  ends_at: string | null;
  duration_minutes: number;
  monitoring_mode: string;
};

export type CandidateDashboard = {
  candidate: { candidate_id: string; full_name: string; email: string; status: string };
  assigned_examinations: AssignedExamination[];
  consent: { accepted: boolean; consent_version: string } | null;
  device_check: { passed: boolean; browser_name: string } | null;
  camera_selection: { camera_selection_id: string; label: string | null; camera_count: number } | null;
  camera_permission: { granted: boolean; status: string } | null;
  active_session: { session_id: string; examination_id: string; status: string } | null;
  readiness: Record<string, boolean>;
};

async function candidateRequest<T>(path: string, accessToken: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${getApiBaseUrl()}${path}`, {
    ...init,
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${accessToken}`,
      ...(init?.headers ?? {}),
    },
    cache: "no-store",
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(body.detail ?? `Candidate workflow request failed with ${response.status}.`);
  }
  return response.json() as Promise<T>;
}

export function getApiBaseUrl(): string {
  return process.env.NEXT_PUBLIC_API_BASE_URL ?? "http://localhost:8000";
}

export async function fetchApiHealth(): Promise<ApiHealth> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/health`, { cache: "no-store" });
  if (!response.ok) {
    throw new Error(`SERPS API health check failed with ${response.status}`);
  }
  return response.json() as Promise<ApiHealth>;
}

export async function login(payload: LoginPayload): Promise<TokenResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    throw new Error("Login failed. Check your credentials and institution code.");
  }
  return response.json() as Promise<TokenResponse>;
}

export async function fetchCurrentUser(accessToken: string): Promise<MeResponse> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/auth/me`, {
    headers: { Authorization: `Bearer ${accessToken}` },
    cache: "no-store",
  });
  if (!response.ok) {
    throw new Error("Session validation failed.");
  }
  return response.json() as Promise<MeResponse>;
}

export async function registerCandidate(payload: Record<string, string>): Promise<Record<string, string>> {
  const response = await fetch(`${getApiBaseUrl()}/api/v1/candidate/register`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({}))) as { detail?: string };
    throw new Error(body.detail ?? "Candidate registration failed.");
  }
  return response.json() as Promise<Record<string, string>>;
}

export function fetchCandidateDashboard(accessToken: string): Promise<CandidateDashboard> {
  return candidateRequest("/api/v1/candidate/dashboard", accessToken);
}

export function acceptCandidateConsent(accessToken: string): Promise<unknown> {
  return candidateRequest("/api/v1/candidate/consents", accessToken, {
    method: "POST",
    body: JSON.stringify({
      consent_version: "CONSENT-1.0",
      monitoring_consent: true,
      privacy_notice_accepted: true,
      institutional_policy_accepted: true,
    }),
  });
}

export function submitDeviceCheck(accessToken: string, payload: Record<string, unknown>): Promise<unknown> {
  return candidateRequest("/api/v1/candidate/device-checks", accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function submitCameraSelection(accessToken: string, payload: Record<string, unknown>): Promise<unknown> {
  return candidateRequest("/api/v1/candidate/cameras", accessToken, {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function submitCameraPermission(accessToken: string, status: string): Promise<unknown> {
  return candidateRequest("/api/v1/candidate/camera-permissions", accessToken, {
    method: "POST",
    body: JSON.stringify({ status, user_agent: navigator.userAgent }),
  });
}

export function startCandidateSession(accessToken: string, examinationId: string): Promise<{ session_id: string; candidate_id: string }> {
  return candidateRequest(`/api/v1/candidate/examinations/${examinationId}/start`, accessToken, {
    method: "POST",
    body: JSON.stringify({ deployment_mode: "A" }),
  });
}

export function submitEvidenceEvent(
  accessToken: string,
  payload: { session_id: string; candidate_id: string; event_type: string; description: string; confidence?: number },
): Promise<unknown> {
  return candidateRequest("/api/v1/evidence-events/", accessToken, {
    method: "POST",
    body: JSON.stringify({
      ...payload,
      source_module: "candidate_browser",
      risk_weight: payload.event_type === "camera_disconnected" ? 0.7 : 0.3,
      confidence: payload.confidence ?? 1.0,
    }),
  });
}
