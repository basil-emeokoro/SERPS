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
