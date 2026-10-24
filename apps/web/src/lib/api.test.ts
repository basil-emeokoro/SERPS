import { afterEach, describe, expect, it, vi } from "vitest";
import {
  SessionExpiredError,
  NetworkError,
  RequestCancelledError,
  apiRequest,
  fetchAdminMetrics,
  fetchCandidateWorkspace,
  fetchGovernanceTimeline,
  fetchReviewerQueue,
  fetchSessionReport,
  getApiBaseUrl,
  submitReviewerDecision,
} from "./api";

afterEach(() => { vi.unstubAllGlobals(); vi.unstubAllEnvs(); });

describe("shared operational API client", () => {
  it("falls back to the local FastAPI endpoint", () => { vi.stubEnv("NEXT_PUBLIC_API_BASE_URL", undefined); expect(getApiBaseUrl()).toBe("http://localhost:8000"); });
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


describe("recoverable authentication interruption", () => {
  function storage() {
    const values = new Map([["serps_access_token", "old"], ["serps_refresh_token", "refresh"]]);
    vi.stubGlobal("window", {});
    vi.stubGlobal("sessionStorage", { getItem: (key: string) => values.get(key) ?? null,
      setItem: (key: string, value: string) => values.set(key, value), removeItem: (key: string) => values.delete(key) });
    return values;
  }
  it.each(["network", "server"])("retains credentials on %s refresh failure", async failure => {
    const values = storage();
    const fetcher = vi.fn().mockResolvedValueOnce(new Response("{}", { status: 401 }));
    if (failure === "network") fetcher.mockRejectedValueOnce(new TypeError("offline"));
    else fetcher.mockResolvedValueOnce(new Response("{}", { status: 503 }));
    vi.stubGlobal("fetch", fetcher);
    await expect(apiRequest("/protected")).rejects.not.toBeInstanceOf(SessionExpiredError);
    expect(values.get("serps_refresh_token")).toBe("refresh");
    expect(values.get("serps_access_token")).toBe("old");
  });
  it("does not retry an aborted GET or erase credentials", async () => {
    const values = storage(); const controller = new AbortController(); controller.abort();
    vi.stubGlobal("fetch", vi.fn());
    await expect(apiRequest("/protected", { signal: controller.signal, retry: true })).rejects.toBeInstanceOf(RequestCancelledError);
    expect(fetch).not.toHaveBeenCalled(); expect(values.get("serps_access_token")).toBe("old");
  });
  it("distinguishes transport failure from HTTP rejection", async () => {
    storage(); vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("offline")));
    await expect(apiRequest("/protected")).rejects.toBeInstanceOf(NetworkError);
  });
  it("clears credentials only after definitive refresh rejection", async () => {
    const values = storage(); vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("{}", { status: 401 })));
    await expect(apiRequest("/protected")).rejects.toBeInstanceOf(SessionExpiredError);
    expect(values.size).toBe(0);
  });
});

it("keeps a newer sign-in when an older authenticated request returns 401", async () => {
  const values = new Map([["serps_access_token", "old"], ["serps_refresh_token", "refresh"]]);
  vi.stubGlobal("window", {});
  vi.stubGlobal("sessionStorage", { getItem: (k: string) => values.get(k) ?? null, setItem: (k: string, v: string) => values.set(k, v), removeItem: (k: string) => values.delete(k) });
  const fetcher = vi.fn().mockImplementationOnce(async () => { values.set("serps_access_token", "new-login"); return new Response("{}", { status: 401 }); }).mockResolvedValueOnce(new Response("{}"));
  vi.stubGlobal("fetch", fetcher); await apiRequest("/protected");
  expect(fetcher).toHaveBeenCalledTimes(2);
  expect(fetcher.mock.calls[1][1].headers.Authorization).toBe("Bearer new-login");
  expect(values.get("serps_access_token")).toBe("new-login");
});
