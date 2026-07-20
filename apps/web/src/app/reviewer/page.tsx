"use client";

import Link from "next/link";
import { FormEvent, useCallback, useEffect, useState } from "react";
import { PortalShell } from "../../components/PortalShell";
import { EmptyState, ErrorState, LoadingState, RiskIndicator, StatusBadge } from "../../components/OperationalStates";
import { fetchReviewerQueue } from "../../lib/api";
import type { ReviewerQueueItem } from "../../lib/contracts";

export default function ReviewerPortalPage() {
  const [sessions, setSessions] = useState<ReviewerQueueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [query, setQuery] = useState("");
  const load = useCallback(async (filter = "") => { await Promise.resolve(); setLoading(true); try { setSessions(await fetchReviewerQueue(filter)); setError(""); } catch (reason) { setError(reason instanceof Error ? reason.message : "Reviewer queue unavailable."); } finally { setLoading(false); } }, []);
  useEffect(() => { const task = window.setTimeout(() => void load(), 0); return () => window.clearTimeout(task); }, [load]);
  function filter(event: FormEvent<HTMLFormElement>) { event.preventDefault(); void load(query); }

  return <PortalShell allowedRoles={["Reviewer/Proctor", "Administrator", "System Administrator"]} title="Reviewer Operational Portal" badge="Reviewer" summary="Live governance queue for evidence-led, human-controlled session review.">
    <form className="filter-bar" onSubmit={filter} aria-label="Reviewer queue filters"><label>Risk level<select onChange={(event) => setQuery((current) => new URLSearchParams({ ...Object.fromEntries(new URLSearchParams(current)), risk_level: event.target.value }).toString())}><option value="">All levels</option>{["Low", "Moderate", "High", "Critical"].map((level) => <option key={level}>{level}</option>)}</select></label><label>Review status<select onChange={(event) => setQuery((current) => new URLSearchParams({ ...Object.fromEntries(new URLSearchParams(current)), unresolved: event.target.value }).toString())}><option value="">All</option><option value="true">Unresolved</option><option value="false">Resolved / not required</option></select></label><label>Session state<select onChange={(event) => setQuery((current) => new URLSearchParams({ ...Object.fromEntries(new URLSearchParams(current)), active_session: event.target.value }).toString())}><option value="">All</option><option value="true">Active</option><option value="false">Completed / inactive</option></select></label><button type="submit">Apply filters</button></form>
    {loading ? <LoadingState label="Loading reviewer session queue..." /> : error ? <ErrorState message={error} onRetry={() => void load(query)} /> : sessions.length === 0 ? <EmptyState title="No reviewer sessions" detail="No institution-scoped sessions match the selected filters." /> : <section className="queue-list" aria-label="Reviewer sessions">{sessions.map((session) => <article className="queue-card" key={session.session_id}><div className="queue-main"><div><StatusBadge label={session.reviewer_action_status.replaceAll("_", " ")} tone={session.reviewer_action_status === "action_required" ? "danger" : "neutral"} /><h2>{session.candidate_name}</h2><p>{session.examination} · {session.session_status}</p></div><RiskIndicator level={session.latest_risk_level} score={session.latest_risk_score} /></div><div className="camera-status-row"><span>Primary: <strong>{session.primary_camera_status}</strong></span><span>Secondary: <strong>{session.secondary_camera_status}</strong></span><span>Latest event: <strong>{session.latest_event_timestamp ? new Date(session.latest_event_timestamp).toLocaleString() : "None"}</strong></span></div><p>{session.assessment_explanation ?? "No contextual explanation is available."}</p><div className="queue-footer"><span>Recommendation: {session.agent_recommendation ?? "Unavailable"}</span><span>IPIME: {session.policy_outcome ?? "Unavailable"}</span><Link className="button-link" href={`/reviewer/sessions/${session.session_id}`}>Open dual-view review</Link></div></article>)}</section>}
  </PortalShell>;
}
