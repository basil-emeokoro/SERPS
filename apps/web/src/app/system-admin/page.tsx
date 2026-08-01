"use client";

import { useCallback, useEffect, useState } from "react";
import { EmptyState, ErrorState, LoadingState, StatusBadge } from "../../components/OperationalStates";
import { PortalShell } from "../../components/PortalShell";
import { decideRegistration, fetchRegistrations } from "../../lib/api";
import type { RegistrationRequest } from "../../lib/contracts";

export default function SystemAdminPortalPage() {
  const [registrations, setRegistrations] = useState<RegistrationRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [status, setStatus] = useState("Review pending institutional access requests.");
  const load = useCallback(async () => { setLoading(true); try { setRegistrations(await fetchRegistrations()); setError(""); } catch (reason) { setError(reason instanceof Error ? reason.message : "Registration requests unavailable."); } finally { setLoading(false); } }, []);
  useEffect(() => { const task = window.setTimeout(() => void load(), 0); return () => window.clearTimeout(task); }, [load]);

  async function decide(item: RegistrationRequest, decision: "approve" | "reject") {
    const rationale = window.prompt(`${decision === "approve" ? "Approval" : "Rejection"} rationale for ${item.email}:`);
    if (!rationale || rationale.trim().length < 8) { setStatus("A substantive rationale of at least eight characters is required."); return; }
    try { await decideRegistration(item.registration_id, decision, rationale.trim()); setStatus(`${item.email} ${decision === "approve" ? "approved" : "rejected"}.`); await load(); }
    catch (reason) { setStatus(reason instanceof Error ? reason.message : "Decision could not be recorded."); }
  }

  return <PortalShell allowedRoles={["System Administrator"]} title="System Administrator Portal" badge="System Administrator" summary="System-level registration approval, authorised identity, role and audit oversight.">
    <section className="status-grid"><article className="card"><span className="badge">Institutions</span><h2>Institution records</h2><p>Institutional scopes separate identities, examinations and governance records.</p></article><article className="card"><span className="badge">Users & Roles</span><h2>Controlled approval</h2><p>Reviewer and administrator roles are assigned only after a System Administrator decision.</p></article><article className="card"><span className="badge">Audit</span><h2>Security and governance audit</h2><p>Registration decisions and identity events create append-only audit records.</p></article></section>
    <p className="workflow-status" role="status">{status}</p>
    {loading ? <LoadingState label="Loading registration requests..." /> : error ? <ErrorState message={error} onRetry={() => void load()} /> : <section className="card"><div className="section-heading"><div><span className="badge">Account lifecycle</span><h2>Registration and approval queue</h2></div><StatusBadge label={`${registrations.filter((item) => item.status === "pending_approval").length} pending`} tone="warning" /></div>{registrations.length ? <div className="oversight-table" role="table" aria-label="System registration requests">{registrations.map((item) => <div className="oversight-row registration-row" role="row" key={item.registration_id}><div role="cell"><strong>{item.email}</strong><span>{item.account_type} · {new Date(item.requested_at).toLocaleString()}</span></div><div role="cell">{item.status.replaceAll("_", " ")}</div><div role="cell">Prototype verification: {item.prototype_verified ? "complete" : "not applicable"}</div>{item.status === "pending_approval" ? <div className="row-actions"><button onClick={() => void decide(item, "approve")}>Approve</button><button className="danger-action" onClick={() => void decide(item, "reject")}>Reject</button></div> : <StatusBadge label={item.status.replaceAll("_", " ")} tone={item.status === "active" ? "success" : item.status === "rejected" ? "danger" : "neutral"} />}</div>)}</div> : <EmptyState title="No registration requests" detail="No candidate, reviewer, or administrator requests have been recorded." />}</section>}
  </PortalShell>;
}
