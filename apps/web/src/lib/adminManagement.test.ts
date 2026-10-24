import { describe, expect, it } from "vitest";
import { cohortConfirmation, confirmCohortAndRefresh, errorFeedback, initialAdminDisclosureState, runMutationWithRefresh, successFeedback, toggleAdminDisclosure } from "./adminManagement";
import type { CohortPreview } from "./api";

const preview = (eligible_count: number): CohortPreview => ({ examination_id: "EXAM", course_id: "COURSE", monitoring_mode: "A", candidates: [], eligible_count, already_assigned_count: eligible_count ? 0 : 1, ineligible_count: 0, created_count: 0 });

describe("administrator examination-management interaction state", () => {
  it("starts creation and registration forms collapsed and toggles each independently", () => {
    const initial = initialAdminDisclosureState();
    expect(initial).toEqual({ examination: false, course: false, registration: false });
    expect(toggleAdminDisclosure(initial, "examination")).toEqual({ examination: true, course: false, registration: false });
    expect(toggleAdminDisclosure(initial, "course")).toEqual({ examination: false, course: true, registration: false });
    expect(toggleAdminDisclosure(initial, "registration")).toEqual({ examination: false, course: false, registration: true });
  });

  it.each([
    "Examination DEM102 created successfully.",
    "Course CSC101 created successfully.",
    "Candidate registered for CSC101 successfully.",
    "Examination DEM102 assigned successfully.",
    "2 eligible candidate assignment(s) created successfully.",
  ])("produces success feedback for %s", (message) => {
    expect(successFeedback(message)).toEqual({ tone: "success", message });
  });

  it.each([
    ["Duplicate examination code.", "Examination could not be created."],
    ["Duplicate course code.", "Course could not be created."],
    ["Registration already exists.", "Course registration failed."],
    ["Assignment already exists.", "Assignment could not be created."],
    ["Cohort assignment failed transactionally.", "Cohort assignment failed."],
  ])("surfaces backend mutation error %s", (backendMessage, fallback) => {
    expect(errorFeedback(new Error(backendMessage), fallback)).toEqual({ tone: "error", message: backendMessage });
  });

  it("disables zero-eligible confirmation with an explanation", () => {
    expect(cohortConfirmation(preview(0))).toEqual({ disabled: true, label: "Confirm cohort assignment", explanation: "No eligible unassigned candidates are available for confirmation." });
  });

  it("enables positive cohort confirmation with the resolved count", () => {
    expect(cohortConfirmation(preview(2))).toEqual({ disabled: false, label: "Confirm assignment of 2 eligible candidate(s)", explanation: null });
  });

  it("invokes cohort assignment then refreshes the preview", async () => {
    const calls: string[] = [];
    const assigned = { ...preview(2), created_count: 2 };
    const refreshed = { ...preview(0), already_assigned_count: 3 };
    const result = await confirmCohortAndRefresh("COURSE", "EXAM", async () => { calls.push("assign"); return assigned; }, async () => { calls.push("preview"); return refreshed; });
    expect(calls).toEqual(["assign", "preview"]);
    expect(result).toEqual({ result: assigned, refreshed });
  });

  it("refreshes administrator state only after a successful mutation", async () => {
    const calls: string[] = [];
    await expect(runMutationWithRefresh(async () => { calls.push("mutate"); return "created"; }, async () => { calls.push("refresh"); })).resolves.toBe("created");
    expect(calls).toEqual(["mutate", "refresh"]);
    calls.length = 0;
    await expect(runMutationWithRefresh(async () => { throw new Error("backend failure"); }, async () => { calls.push("refresh"); })).rejects.toThrow("backend failure");
    expect(calls).toEqual([]);
  });
});
