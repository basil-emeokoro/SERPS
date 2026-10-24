// @vitest-environment jsdom
import React from "react";
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, expect, it, vi } from "vitest";
import ReviewerSessionPage from "../app/reviewer/sessions/[sessionId]/page";
import { fetchReviewerSession, submitReviewerDecision } from "./api";
vi.mock("./api", () => ({ fetchReviewerSession: vi.fn(), submitReviewerDecision: vi.fn(), generateSessionReport: vi.fn() }));
vi.mock("next/navigation", () => ({ useParams: () => ({ sessionId: "S" }) }));
vi.mock("../components/PortalShell", () => ({ PortalShell: ({ children }: { children: React.ReactNode }) => <main>{children}</main> }));
vi.mock("../components/SessionOperationalView", () => ({ SessionOperationalView: ({ detail }: { detail: { latest_policy_evaluation: { evaluation_id: string } } }) => <p>Visible chain {detail.latest_policy_evaluation.evaluation_id}</p> }));
const detail = (id: string) => ({ latest_assessment: { assessment_id: "A"+id }, latest_recommendation: { recommendation_id: "R"+id, assessment_id: "A"+id }, latest_policy_evaluation: { evaluation_id: id, recommendation_id: "R"+id }, identity_reauthentication: { session_id: "S", state: "manual_review", required: true, assessment_id: "ORIGIN-A", recommendation_id: "ORIGIN-R", policy_evaluation_id: "ORIGIN-P" } });
beforeEach(() => { vi.useFakeTimers(); vi.mocked(fetchReviewerSession).mockReset(); vi.mocked(submitReviewerDecision).mockReset().mockResolvedValue({}); });
afterEach(() => { cleanup(); vi.useRealTimers(); });
it("keeps rationale and detail mounted while polling and submits the confirmed originating identity chain", async () => {
  vi.mocked(fetchReviewerSession).mockResolvedValueOnce(detail("P1") as never).mockResolvedValue(detail("P2") as never);
  render(<ReviewerSessionPage />);
  await act(async () => { await vi.advanceTimersByTimeAsync(0); });
  fireEvent.change(screen.getByLabelText("Decision"), { target: { value: "REQUEST_REAUTHENTICATION" } });
  const rationale = screen.getByLabelText("Mandatory rationale") as HTMLTextAreaElement;
  fireEvent.change(rationale, { target: { value: "Review the original identity concern." } });
  fireEvent.click(screen.getByText("Review and submit"));
  await act(async () => { await vi.advanceTimersByTimeAsync(10000); });
  expect(screen.getByText("Visible chain P2")).toBeTruthy();
  expect(screen.getByLabelText("Mandatory rationale")).toBe(rationale);
  expect(rationale.value).toBe("Review the original identity concern.");
  await act(async () => { fireEvent.click(screen.getByText("Persist decision")); });
  expect(submitReviewerDecision).toHaveBeenCalledExactlyOnceWith("S", { assessment_id: "ORIGIN-A", recommendation_id: "ORIGIN-R", policy_evaluation_id: "ORIGIN-P", decision: "REQUEST_REAUTHENTICATION", rationale: "Review the original identity concern." });
  expect(screen.getByText("Reviewer decision persisted as a new immutable record.")).toBeTruthy();
});
it("does not retarget a confirmed ordinary decision when newer evidence arrives", async () => {
  vi.mocked(fetchReviewerSession).mockResolvedValueOnce({ ...detail("P1"), identity_reauthentication: undefined } as never).mockResolvedValue({ ...detail("P2"), identity_reauthentication: undefined } as never);
  render(<ReviewerSessionPage />);
  await act(async () => { await vi.advanceTimersByTimeAsync(0); });
  fireEvent.change(screen.getByLabelText("Decision"), { target: { value: "CONTINUE" } });
  fireEvent.change(screen.getByLabelText("Mandatory rationale"), { target: { value: "Reviewed initial context." } });
  fireEvent.click(screen.getByText("Review and submit"));
  await act(async () => { await vi.advanceTimersByTimeAsync(10000); fireEvent.click(screen.getByText("Persist decision")); });
  expect(submitReviewerDecision).toHaveBeenCalledWith("S", expect.objectContaining({ assessment_id: "AP1", recommendation_id: "RP1", policy_evaluation_id: "P1" }));
});
