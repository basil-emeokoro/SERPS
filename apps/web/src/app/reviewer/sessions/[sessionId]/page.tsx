"use client";

import { useParams } from "next/navigation";
import { FormEvent, useCallback, useRef, useState } from "react";
import { PortalShell } from "../../../../components/PortalShell";
import { ConfirmationDialog, ErrorState, LoadingState, StatusBadge } from "../../../../components/OperationalStates";
import { SessionOperationalView } from "../../../../components/SessionOperationalView";
import { fetchReviewerSession, generateSessionReport, submitReviewerDecision } from "../../../../lib/api";
import { useReviewerResource } from "../../../../lib/useReviewerResource";
import { reviewerDetailPresentation, validateReviewerDecision } from "../../../../lib/operational";

const decisions = ["CONTINUE", "REQUEST_REAUTHENTICATION", "ACKNOWLEDGE", "ESCALATE", "REQUEST_MORE_EVIDENCE"];

function ReviewerSessionContent({ sessionId }: { sessionId: string }) {
  const fetchDetail = useCallback((id: string, signal: AbortSignal) => fetchReviewerSession(id, "reviewer", signal), []);
  const { data: detail, pending: loading, error, refresh: load } = useReviewerResource(sessionId, fetchDetail);
  const [decision, setDecision] = useState("");
  const [rationale, setRationale] = useState("");
  const [validation, setValidation] = useState("");
  const [confirm, setConfirm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState("");
  const submitInFlight = useRef(false);
  const [prepared, setPrepared] = useState<Record<string, unknown> | null>(null);
  function prepare(event: FormEvent) {
    event.preventDefault();
    const message = validateReviewerDecision(decision, rationale);
    setValidation(message ?? "");
    if (message || !detail?.latest_assessment || !detail.latest_recommendation || !detail.latest_policy_evaluation) return;
    const identity = detail.identity_reauthentication?.required ? detail.identity_reauthentication : null;
    setPrepared({ assessment_id: identity?.assessment_id ?? detail.latest_assessment.assessment_id,
      recommendation_id: identity?.recommendation_id ?? detail.latest_recommendation.recommendation_id,
      policy_evaluation_id: identity?.policy_evaluation_id ?? detail.latest_policy_evaluation.evaluation_id,
      decision, rationale });
    setConfirm(true);
  }
  async function persistDecision() {
    if (!prepared || submitInFlight.current) return;
    submitInFlight.current = true;
    setConfirm(false); setSubmitting(true); setSuccess("");
    try {
      await submitReviewerDecision(sessionId, prepared);
      setSuccess("Reviewer decision persisted as a new immutable record.");
      setDecision(""); setRationale(""); setPrepared(null);
      await load();
    } catch (reason) { setValidation(reason instanceof Error ? reason.message : "Decision could not be persisted."); }
    finally { submitInFlight.current = false; setSubmitting(false); }
  }
  async function report() { try { const result = await generateSessionReport(sessionId); setSuccess(`Structured report generated: ${String(result.report_id)}`); await load(); } catch (reason) { setValidation(reason instanceof Error ? reason.message : "Report generation failed."); } }

  const presentation = reviewerDetailPresentation(detail !== null, loading, error);

  return <PortalShell allowedRoles={["Reviewer/Proctor", "System Administrator"]} title="Reviewer Session Review" badge="Human decision" summary="Unified dual-camera metadata, explainable governance history and append-only reviewer action.">
    {presentation === "loading" ? <LoadingState label="Loading evidence and governance detail..." /> : presentation === "error" || !detail ? <ErrorState message={error || "Session detail unavailable."} onRetry={() => void load()} /> : <><SessionOperationalView detail={detail} />{error && <p role="alert">Refresh failed: {error}. The loaded review and rationale remain available.</p>}<section className="card decision-card"><div className="section-heading"><div><span className="badge">Reviewer authority</span><h2>Record operational decision</h2></div><button onClick={() => void report()}>Generate structured report</button></div>{success && <p className="success-message" role="status"><StatusBadge label="Persisted" tone="success" /> {success}</p>}{detail.identity_reauthentication?.required && <p role="status">Identity assurance: {detail.identity_reauthentication.state}. This decision targets its originating policy evaluation. CONTINUE authorises continuation without claiming a biometric match; REQUEST_REAUTHENTICATION authorises a fresh bounded attempt; ESCALATE keeps human review required.</p>}<form onSubmit={prepare}><label>Decision<select value={decision} onChange={(event) => setDecision(event.target.value)} required><option value="">Select decision</option>{decisions.map((value) => <option key={value}>{value}</option>)}</select></label><label>Mandatory rationale<textarea value={rationale} onChange={(event) => setRationale(event.target.value)} rows={5} required /></label>{validation && <p className="danger-text" role="alert">{validation}</p>}<button className="primary-action" disabled={submitting || !detail.latest_policy_evaluation} type="submit">{submitting ? "Persisting..." : "Review and submit"}</button></form></section><ConfirmationDialog open={confirm} title="Confirm reviewer decision" detail={`${String(prepared?.decision ?? "")}: ${String(prepared?.rationale ?? "")}`} confirmLabel="Persist decision" onConfirm={() => void persistDecision()} onCancel={() => setConfirm(false)} /></>}
  </PortalShell>;
}

export default function ReviewerSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  return <ReviewerSessionContent key={sessionId} sessionId={sessionId} />;
}
