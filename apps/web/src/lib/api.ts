export type ApiHealth = {
  status: string;
  service: string;
  version: string;
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
