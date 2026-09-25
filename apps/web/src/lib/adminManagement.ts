import type { CohortPreview } from "./api";

export type AdminDisclosure = "examination" | "course" | "registration";
export type AdminDisclosureState = Record<AdminDisclosure, boolean>;
export type OperationFeedback = { tone: "success" | "error"; message: string } | null;

export const initialAdminDisclosureState = (): AdminDisclosureState => ({ examination: false, course: false, registration: false });

export function toggleAdminDisclosure(state: AdminDisclosureState, key: AdminDisclosure): AdminDisclosureState {
  return { ...state, [key]: !state[key] };
}

export function successFeedback(message: string): OperationFeedback { return { tone: "success", message }; }
export function errorFeedback(reason: unknown, fallback: string): OperationFeedback {
  return { tone: "error", message: reason instanceof Error ? reason.message : fallback };
}

export function cohortConfirmation(preview: CohortPreview | null): { disabled: boolean; label: string; explanation: string | null } {
  if (!preview) return { disabled: true, label: "Confirm cohort assignment", explanation: null };
  if (preview.eligible_count === 0) return { disabled: true, label: "Confirm cohort assignment", explanation: "No eligible unassigned candidates are available for confirmation." };
  return { disabled: false, label: `Confirm assignment of ${preview.eligible_count} eligible candidate(s)`, explanation: null };
}

export async function runMutationWithRefresh<T>(mutation: () => Promise<T>, refresh: () => Promise<void>): Promise<T> {
  const result = await mutation();
  await refresh();
  return result;
}

export async function confirmCohortAndRefresh(
  courseId: string,
  examinationId: string,
  assign: (courseId: string, examinationId: string) => Promise<CohortPreview>,
  preview: (courseId: string, examinationId: string) => Promise<CohortPreview>,
): Promise<{ result: CohortPreview; refreshed: CohortPreview }> {
  const result = await assign(courseId, examinationId);
  const refreshed = await preview(courseId, examinationId);
  return { result, refreshed };
}
