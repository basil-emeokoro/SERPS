// @vitest-environment jsdom
import React from "react";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import ReviewerPortalPage from "../app/reviewer/page";
import { fetchReviewerQueue } from "./api";
vi.mock("./api", () => ({ fetchReviewerQueue: vi.fn() }));
vi.mock("next/link", () => ({ default: ({ children, href }: { children: React.ReactNode; href: string }) => <a href={href}>{children}</a> }));
vi.mock("../components/PortalShell", () => ({ PortalShell: ({ children }: { children: React.ReactNode }) => <main>{children}</main> }));
const rows = [{ session_id: "S", candidate_name: "Synthetic candidate", examination: "Synthetic examination", session_status: "active", reviewer_action_status: "action_required", latest_risk_level: "High", latest_risk_score: 0.7, primary_camera_status: "connected", secondary_camera_status: "not_used", latest_event_timestamp: null, assessment_explanation: "Context", agent_recommendation: "NOTIFY_REVIEWER", policy_outcome: "NOTIFY_REVIEWER" }];
beforeEach(() => { vi.useFakeTimers(); vi.mocked(fetchReviewerQueue).mockReset(); });
afterEach(() => { cleanup(); vi.useRealTimers(); });
it("keeps the populated queue visible while a background refresh is unresolved", async () => {
  vi.mocked(fetchReviewerQueue).mockResolvedValueOnce(rows as never).mockImplementationOnce(() => new Promise(() => undefined));
  render(<ReviewerPortalPage />);
  await act(async () => { await vi.advanceTimersByTimeAsync(0); });
  expect(screen.getByText("Synthetic candidate")).toBeTruthy();
  await act(async () => { await vi.advanceTimersByTimeAsync(10000); });
  expect(screen.getByText("Synthetic candidate")).toBeTruthy();
});

it("does not allow an older filter response to overwrite the current selection", async () => {
  let finishOld: (value: never) => void = () => undefined;
  vi.mocked(fetchReviewerQueue).mockImplementationOnce(() => new Promise((resolve) => { finishOld = resolve; })).mockResolvedValueOnce([{ ...rows[0], candidate_name: "Current result" }] as never);
  render(<ReviewerPortalPage />);
  await act(async () => { await vi.advanceTimersByTimeAsync(0); });
  fireEvent.change(screen.getByLabelText("Risk level"), { target: { value: "High" } });
  await act(async () => { await vi.advanceTimersByTimeAsync(0); });
  expect(screen.getByText("Current result")).toBeTruthy();
  await act(async () => { finishOld(rows as never); });
  expect(screen.queryByText("Synthetic candidate")).toBeNull();
  expect(screen.getByText("Current result")).toBeTruthy();
});
it("removes boolean filters when All is selected and retains data after refresh errors", async () => {
  vi.mocked(fetchReviewerQueue).mockResolvedValue(rows as never);
  render(<ReviewerPortalPage />);
  await act(async () => { await vi.advanceTimersByTimeAsync(0); });
  fireEvent.change(screen.getByLabelText("Review status"), { target: { value: "true" } });
  await act(async () => { await vi.advanceTimersByTimeAsync(0); });
  expect(vi.mocked(fetchReviewerQueue).mock.calls.at(-1)?.[0]).toBe("unresolved=true");
  fireEvent.change(screen.getByLabelText("Review status"), { target: { value: "" } });
  await act(async () => { await vi.advanceTimersByTimeAsync(0); });
  expect(vi.mocked(fetchReviewerQueue).mock.calls.at(-1)?.[0]).toBe("");
  vi.mocked(fetchReviewerQueue).mockRejectedValueOnce(new Error("Synthetic connection failure"));
  await act(async () => { await vi.advanceTimersByTimeAsync(10000); });
  expect(screen.getByText("Synthetic candidate")).toBeTruthy();
  expect(screen.getByRole("alert").textContent).toContain("Synthetic connection failure");
});
