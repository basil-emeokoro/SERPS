import { PortalShell } from "../../components/PortalShell";

export default function CandidatePortalPage() {
  return (
    <PortalShell
      allowedRoles={["Candidate"]}
      title="Candidate Portal"
      badge="Candidate"
      summary="Candidate-facing session readiness without exposure to reviewer intelligence, CIE internals or policy rules."
    >
      <section className="status-grid">
        <article className="card">
          <span className="badge">Profile</span>
          <h2>Profile summary</h2>
          <p>Candidate biodata, institutional identifier and enrolment status will be shown here after candidate self-profile binding.</p>
        </article>
        <article className="card">
          <span className="badge">Assignments</span>
          <h2>Assigned examinations</h2>
          <p>Eligible exams and session readiness will be loaded from `/api/v1/examinations` and `/api/v1/examination-sessions`.</p>
        </article>
        <article className="card">
          <span className="badge">Due Process</span>
          <h2>Candidate notices</h2>
          <p>Incident acknowledgement workflows remain future IPIME migration work and will not accuse candidates automatically.</p>
        </article>
      </section>
    </PortalShell>
  );
}
