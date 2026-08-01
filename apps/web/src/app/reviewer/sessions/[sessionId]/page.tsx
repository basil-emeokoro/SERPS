"use client";

import { useParams } from "next/navigation";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { PortalShell } from "../../../../components/PortalShell";
import { ConfirmationDialog, ErrorState, LoadingState, StatusBadge } from "../../../../components/OperationalStates";
import { SessionOperationalView } from "../../../../components/SessionOperationalView";
import { fetchReviewerSession, generateSessionReport, submitReviewerDecision } from "../../../../lib/api";
import type { OperationalSessionDetail } from "../../../../lib/contracts";
import { validateReviewerDecision } from "../../../../lib/operational";

const decisions = ["CONTINUE", "REQUEST_REAUTHENTICATION", "ACKNOWLEDGE", "ESCALATE", "REQUEST_MORE_EVIDENCE"];

export default function ReviewerSessionPage() {
  const { sessionId } = useParams<{ sessionId: string }>();
  const [detail, setDetail] = useState<OperationalSessionDetail | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [decision, setDecision] = useState("");
  const [rationale, setRationale] = useState("");
  const [validation, setValidation] = useState("");
  const [confirm, setConfirm] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState("");
  const load = useCallback(async () => { await Promise.resolve(); setLoading(true); try { setDetail(await fetchReviewerSession(sessionId)); setError(""); } catch (reason) { setError(reason instanceof Error ? reason.message : "Session review unavailable."); } finally { setLoading(false); } }, [sessionId]);
  useEffect(() => { const task = window.setTimeout(() => void load(), 0); const poll = window.setInterval(() => void load(), 10000); return () => { window.clearTimeout(task); window.clearInterval(poll); }; }, [load]);
  function prepare(event: FormEvent) { event.preventDefault(); const message = validateReviewerDecision(decision, rationale); setValidation(message ?? ""); if (!message) setConfirm(true); }
  async function persistDecision() {
    if (!detail?.latest_assessment || !detail.latest_recommendation || !detail.latest_policy_evaluation) return;
    setConfirm(false); setSubmitting(true); setSuccess("");
    try { await submitReviewerDecision(sessionId, { assessment_id: detail.latest_assessment.assessment_id, recommendation_id: detail.latest_recommendation.recommendation_id, policy_evaluation_id: detail.latest_policy_evaluation.evaluation_id, decision, rationale }); setSuccess("Reviewer decision persisted as a new immutable record."); setDecision(""); setRationale(""); await load(); }
    catch (reason) { setValidation(reason instanceof Error ? reason.message : "Decision could not be persisted."); }
    finally { setSubmitting(false); }
  }
  async function report() { try { const result = await generateSessionReport(sessionId); setSuccess(`Structured report generated: ${String(result.report_id)}`); await load(); } catch (reason) { setValidation(reason instanceof Error ? reason.message : "Report generation failed."); } }

  return <PortalShell allowedRoles={["Reviewer/Proctor", "System Administrator"]} title="Reviewer Session Review" badge="Human decision" summary="Unified dual-camera metadata, explainable governance history and append-only reviewer action.">
    {loading ? <LoadingState label="Loading evidence and governance detail..." /> : error || !detail ? <ErrorState message={error || "Session detail unavailable."} onRetry={() => void load()} /> : <><SessionOperationalView detail={detail} /><section className="card decision-card"><div className="section-heading"><div><span className="badge">Reviewer authority</span><h2>Record operational decision</h2></div><button onClick={() => void report()}>Generate structured report</button></div>{success && <p className="success-message" role="status"><StatusBadge label="Persisted" tone="success" /> {success}</p>}<form onSubmit={prepare}><label>Decision<select value={decision} onChange={(event) => setDecision(event.target.value)} required><option value="">Select decision</option>{decisions.map((value) => <option key={value}>{value}</option>)}</select></label><label>Mandatory rationale<textarea value={rationale} onChange={(event) => setRationale(event.target.value)} rows={5} required /></label>{validation && <p className="danger-text" role="alert">{validation}</p>}<button className="primary-action" disabled={submitting || !detail.latest_policy_evaluation} type="submit">{submitting ? "Persisting..." : "Review and submit"}</button></form></section><ConfirmationDialog open={confirm} title="Confirm reviewer decision" detail={`${decision}: ${rationale}`} confirmLabel="Persist decision" onConfirm={() => void persistDecision()} onCancel={() => setConfirm(false)} /></>}
  </PortalShell>;
}
