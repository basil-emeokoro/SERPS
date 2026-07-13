import { PortalShell } from "../../components/PortalShell";

export default function AdminPortalPage() {
  return (
    <PortalShell
      allowedRoles={["Administrator", "System Administrator"]}
      title="Administrator Portal"
      badge="Administrator"
      summary="Institution-scoped operational management for candidates, examinations, assignments and sessions."
    >
      <section className="status-grid">
        <article className="card">
          <span className="badge">Candidates</span>
          <h2>Candidate registry</h2>
          <p>Use `/api/v1/candidates` for duplicate-safe candidate creation, listing and updates.</p>
        </article>
        <article className="card">
          <span className="badge">Examinations</span>
          <h2>Exam management</h2>
          <p>Use `/api/v1/examinations` for institution-owned exams, policy profiles and monitoring modes.</p>
        </article>
        <article className="card">
          <span className="badge">Sessions</span>
          <h2>Session lifecycle</h2>
          <p>Use `/api/v1/examination-sessions` for controlled state transitions and duplicate active-session prevention.</p>
        </article>
      </section>
    </PortalShell>
  );
}
