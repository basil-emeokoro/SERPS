import { afterEach, describe, expect, it, vi } from "vitest";
import {
  SessionExpiredError,
  apiRequest,
  fetchAdminMetrics,
  fetchCandidateWorkspace,
  fetchGovernanceTimeline,
  fetchReviewerQueue,
  fetchSessionReport,
  getApiBaseUrl,
  submitReviewerDecision,
} from "./api";

afterEach(() => vi.unstubAllGlobals());

describe("shared operational API client", () => {
  it("falls back to the local FastAPI endpoint", () => expect(getApiBaseUrl()).toBe("http://localhost:8000"));
  it("parses access-denied errors consistently", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Insufficient permissions." }), { status: 403, headers: { "Content-Type": "application/json" } })));
    await expect(apiRequest("/api/v1/admin/metrics")).rejects.toEqual(
      expect.objectContaining({ status: 403, message: "Insufficient permissions." }),
    );
  });
  it("classifies authentication expiry", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(JSON.stringify({ detail: "Invalid or expired credentials." }), { status: 401, headers: { "Content-Type": "application/json" } })));
    await expect(apiRequest("/api/v1/reviewer/sessions")).rejects.toBeInstanceOf(SessionExpiredError);
  });
  it("rotates the refresh token and retries an authenticated request once", async () => {
    const values = new Map([
      ["serps_access_token", "expired-access"],
      ["serps_refresh_token", "valid-refresh"],
    ]);
    vi.stubGlobal("window", {});
    vi.stubGlobal("sessionStorage", {
      getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => values.set(key, value),
      removeItem: (key: string) => values.delete(key),
    });
    const request = vi.fn()
      .mockResolvedValueOnce(new Response(JSON.stringify({ detail: "Invalid or expired credentials." }), { status: 401, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response(JSON.stringify({ access_token: "fresh-access", refresh_token: "fresh-refresh", token_type: "bearer", expires_in: 1200 }), { status: 200, headers: { "Content-Type": "application/json" } }))
      .mockResolvedValueOnce(new Response("{}", { status: 201, headers: { "Content-Type": "application/json" } }));
    vi.stubGlobal("fetch", request);

    await expect(apiRequest("/api/v1/evidence-events/", { method: "POST", body: "{}" })).resolves.toEqual({});
    expect(request).toHaveBeenCalledTimes(3);
    expect(request.mock.calls[1][0]).toContain("/api/v1/auth/refresh");
    expect(request.mock.calls[2][1]).toEqual(expect.objectContaining({ headers: expect.objectContaining({ Authorization: "Bearer fresh-access" }) }));
    expect(values.get("serps_refresh_token")).toBe("fresh-refresh");
  });
  it("retrieves the reviewer queue through the shared client", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("[]", { status: 200, headers: { "Content-Type": "application/json" } })));
    await expect(fetchReviewerQueue("unresolved=true")).resolves.toEqual([]);
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/api/v1/reviewer/sessions?unresolved=true"), expect.any(Object));
  });
  it("submits reviewer decisions without duplicate fetch implementations", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 201, headers: { "Content-Type": "application/json" } })));
    await submitReviewerDecision("SESSION", { decision: "CONTINUE", rationale: "Evidence reviewed." });
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining("/reviewer-decisions"), expect.objectContaining({ method: "POST" }));
  });
  it.each([
    ["candidate session", () => fetchCandidateWorkspace("SESSION"), "/api/v1/candidate/sessions/SESSION"],
    ["governance timeline", () => fetchGovernanceTimeline("SESSION"), "/governance-timeline"],
    ["administrator metrics", () => fetchAdminMetrics(), "/api/v1/admin/metrics"],
    ["structured report", () => fetchSessionReport("SESSION", "REPORT"), "/reports/REPORT"],
  ])("retrieves %s through the authenticated shared client", async (_label, request, path) => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 200, headers: { "Content-Type": "application/json" } })));
    await request();
    expect(fetch).toHaveBeenCalledWith(expect.stringContaining(path), expect.any(Object));
  });
});
