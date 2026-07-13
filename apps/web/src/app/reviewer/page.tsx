import { PortalShell } from "../../components/PortalShell";

export default function ReviewerPortalPage() {
  return (
    <PortalShell
      allowedRoles={["Reviewer/Proctor", "Administrator", "System Administrator"]}
      title="Reviewer / Proctor Portal"
      badge="Reviewer"
      summary="Reviewer workspace foundation for assigned sessions, evidence review and future CIE/IPIME summaries."
    >
      <section className="status-grid">
        <article className="card">
          <span className="badge">Assigned Sessions</span>
          <h2>Session queue</h2>
          <p>Assignment-scoped session filtering is a Sprint 3 hardening item. This placeholder does not fabricate monitoring data.</p>
        </article>
        <article className="card">
          <span className="badge">Evidence</span>
          <h2>Evidence timeline</h2>
          <p>Raw evidence will remain immutable and reviewer-facing decisions will be captured separately.</p>
        </article>
        <article className="card">
          <span className="badge">Human Review</span>
          <h2>Decision boundary</h2>
          <p>Reviewers make final authorised decisions. CIE and Agentic Decision Support remain advisory after migration.</p>
        </article>
      </section>
    </PortalShell>
  );
}
