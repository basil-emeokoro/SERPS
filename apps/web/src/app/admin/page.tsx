"use client";

import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import { PortalShell } from "../../components/PortalShell";
import { EmptyState, ErrorState, LoadingState, MetricCards, StatusBadge } from "../../components/OperationalStates";
import { fetchAdminMetrics, fetchAdminPolicy, fetchRegistrations, fetchReviewerQueue } from "../../lib/api";
import type { AdministratorMetrics, InstitutionalPolicy, RegistrationRequest, ReviewerQueueItem } from "../../lib/contracts";

export default function AdminPortalPage() {
  const [metrics, setMetrics] = useState<AdministratorMetrics | null>(null);
  const [policy, setPolicy] = useState<InstitutionalPolicy | null>(null);
  const [sessions, setSessions] = useState<ReviewerQueueItem[]>([]);
  const [registrations, setRegistrations] = useState<RegistrationRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [updatedAt, setUpdatedAt] = useState<string | null>(null);
  const load = useCallback(async () => {
    setLoading(true);
    try {
      const [metricData, policyData, sessionData, registrationData] = await Promise.all([fetchAdminMetrics(), fetchAdminPolicy(), fetchReviewerQueue(), fetchRegistrations()]);
      setMetrics(metricData); setPolicy(policyData); setSessions(sessionData); setRegistrations(registrationData); setUpdatedAt(metricData.last_updated_at ?? new Date().toISOString()); setError("");
    } catch (reason) { setError(reason instanceof Error ? reason.message : "Administrator oversight unavailable."); }
    finally { setLoading(false); }
  }, []);
  useEffect(() => { const task = window.setTimeout(() => void load(), 0); const poll = window.setInterval(() => void load(), 10000); return () => { window.clearTimeout(task); window.clearInterval(poll); }; }, [load]);

  return <PortalShell allowedRoles={["Administrator", "System Administrator"]} title="Administrator Oversight" badge="Institution operations" summary="Institution-scoped identity, session, risk, camera-metadata and audit oversight without reviewer decision authority.">
    <div className="refresh-strip"><span>{updatedAt ? `Last updated ${new Date(updatedAt).toLocaleTimeString()}` : "Awaiting live data"}</span><button type="button" title="Refresh administrator state" onClick={() => void load()} disabled={loading}>Refresh</button></div>
    {loading && !metrics ? <LoadingState label="Loading institution metrics..." /> : error || !metrics ? <ErrorState message={error || "Metrics unavailable."} onRetry={() => void load()} /> : <>
      <MetricCards metrics={[{ label: "Active candidates", value: metrics.active_candidates }, { label: "Active sessions", value: metrics.active_sessions }, { label: "Completed sessions", value: metrics.completed_sessions }, { label: "Unresolved cases", value: metrics.unresolved_reviewer_cases }, { label: "Primary cameras connected", value: metrics.connected_primary_cameras }, { label: "Secondary cameras connected", value: metrics.connected_secondary_cameras }, { label: "Camera failures", value: metrics.camera_failure_count }]} />
      <section className="card"><div className="section-heading"><div><span className="badge">Registration lifecycle</span><h2>Institution identity status</h2></div><StatusBadge label={`${registrations.filter((item) => item.status === "pending_approval").length} pending approval`} tone={registrations.some((item) => item.status === "pending_approval") ? "warning" : "neutral"} /></div>{registrations.length ? <div className="oversight-table" role="table" aria-label="Registration lifecycle">{registrations.map((item) => <div className="oversight-row" role="row" key={item.registration_id}><div role="cell"><strong>{item.email}</strong><span>{item.account_type}</span></div><div role="cell">Account: {item.status.replaceAll("_", " ")}</div><div role="cell">Verification: {item.prototype_verified ? "prototype verified" : "pending"}</div><StatusBadge label={item.status.replaceAll("_", " ")} tone={item.status === "active" ? "success" : item.status === "rejected" ? "danger" : "warning"} /></div>)}</div> : <EmptyState title="No registration requests" detail="No institution-scoped registration lifecycle records are available." />}</section>
      <section className="risk-metric-grid">{Object.entries(metrics.risk_counts).map(([level, count]) => <article className={`metric-card risk-${level.toLowerCase()}`} key={level}><span>{level} risk sessions</span><strong>{count}</strong></article>)}</section>
      <section className="two-column"><article className="card"><span className="badge">Institutional policy</span><h2>{policy ? `Version ${policy.policy_version}` : "Unavailable"}</h2>{policy ? <dl className="detail-list"><div><dt>Reviewer threshold</dt><dd>{policy.reviewer_notification_threshold}</dd></div><div><dt>Reauthentication threshold</dt><dd>{policy.reauthentication_threshold}</dd></div><div><dt>Candidate acknowledgement</dt><dd>{policy.candidate_acknowledgement_required ? "Required" : "Not required"}</dd></div><div><dt>Automatic termination</dt><dd>{policy.automatic_exam_termination_allowed ? "Enabled" : "Disabled"}</dd></div></dl> : <p>No active persisted policy exists yet.</p>}</article><article className="card"><span className="badge">Recent audit</span><h2>Governance activity</h2>{metrics.recent_audit_activity.length ? <ul className="compact-list">{metrics.recent_audit_activity.map((item) => <li key={String(item.audit_id)}><strong>{String(item.action)}</strong><span>{new Date(String(item.timestamp)).toLocaleString()}</span></li>)}</ul> : <p>No governance audit activity exists.</p>}</article></section>
      <section className="card"><div className="section-heading"><div><span className="badge">Session oversight</span><h2>Dual-camera operational sessions</h2></div><StatusBadge label={`${sessions.length} sessions`} /></div>{sessions.length ? <div className="oversight-table" role="table" aria-label="Administrator session oversight">{sessions.map((session) => <div className="oversight-row" role="row" key={session.session_id}><div role="cell"><strong>{session.candidate_name}</strong><span>{session.examination}</span></div><div role="cell">Risk: {session.latest_risk_level ?? "Unavailable"}</div><div role="cell">Primary: {session.primary_camera_status}</div><div role="cell">Secondary: {session.secondary_camera_status}</div><Link className="button-link" href={`/admin/sessions/${session.session_id}`}>Inspect</Link></div>)}</div> : <EmptyState title="No sessions" detail="No institution-scoped examination sessions are available." />}</section>
    </>}
  </PortalShell>;
}
