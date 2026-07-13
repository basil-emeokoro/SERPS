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
