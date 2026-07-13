import { getApiBaseUrl } from "../lib/api";

export function HealthCard() {
  return (
    <article className="card">
      <span className="badge">API Boundary</span>
      <h2>FastAPI Service</h2>
      <p>Configured endpoint: {getApiBaseUrl()}/api/v1/health</p>
      <p>Health connectivity is implemented through a reusable API client abstraction.</p>
    </article>
  );
}
