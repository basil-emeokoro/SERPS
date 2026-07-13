import { HealthCard } from "../components/HealthCard";
import Link from "next/link";

const governancePipeline = [
  "Structured Evidence",
  "Contextual Intelligence Engine",
  "Agentic Recommendation",
  "Institutional Policy",
  "Human Review",
];

const portalPanels = [
  {
    title: "Administrator Portal",
    badge: "Admin",
    href: "/admin",
    summary: "Create institutions, staff users, candidates, examinations, assignments and controlled examination sessions.",
    items: ["Institution-scoped RBAC", "Candidate registry", "Exam/session lifecycle", "Audit visibility"],
  },
  {
    title: "Reviewer / Proctor Portal",
    badge: "Reviewer",
    href: "/reviewer",
    summary: "Monitor assigned examination sessions and review evidence without making automated misconduct decisions.",
    items: ["Assigned session queue", "Evidence timeline", "CIE/IPIME summaries", "Reviewer rationale capture"],
  },
  {
    title: "Candidate Portal",
    badge: "Candidate",
    href: "/candidate",
    summary: "Candidate-facing exam flow remains separated from reviewer intelligence and policy internals.",
    items: ["Authentication gate", "Device-check readiness", "Exam session status", "Due-process notices"],
  },
];

const sessionStates = [
  "authentication_pending",
  "device_check_pending",
  "ready",
  "active",
  "paused",
  "completed",
  "terminated",
];

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero" aria-labelledby="hero-title">
        <p className="eyebrow">SERPS POP</p>
        <h1 id="hero-title">Secure Explainable Remote Proctoring System</h1>
        <p>
          Production-oriented prototype foundation preserving the validated SERPS governance pipeline while separating frontend, API,
          persistence and domain logic.
        </p>
        <Link className="hero-link" href="/login">Open authenticated portal login</Link>
      </section>

      <section className="status-grid" aria-label="SERPS POP foundation status">
        <HealthCard />
        {portalPanels.map((panel) => (
          <article className="card portal-card" key={panel.title}>
            <span className="badge">{panel.badge}</span>
            <h2>{panel.title}</h2>
            <p>{panel.summary}</p>
            <ul>
              {panel.items.map((item) => (
                <li key={item}>{item}</li>
              ))}
            </ul>
            <Link className="button-link" href={panel.href}>Open portal foundation</Link>
          </article>
        ))}
      </section>

      <section className="section-card" aria-labelledby="pipeline-title">
        <div>
          <span className="badge">Frozen Governance Pipeline</span>
          <h2 id="pipeline-title">Role-aware workflows still route through SERPS reasoning controls</h2>
          <p>
            Sprint 2 introduces identity, RBAC, candidate, examination and session foundations. It does not move decision authority
            into the portals. Detection modules still produce evidence only; human reviewers remain responsible for final outcomes.
          </p>
        </div>
        <div className="pipeline">
          {governancePipeline.map((step) => (
            <span key={step}>{step}</span>
          ))}
        </div>
      </section>

      <section className="two-column">
        <article className="card">
          <span className="badge">Session Foundation</span>
          <h2>Controlled Session Lifecycle</h2>
          <p>Examination sessions now follow an auditable state model that prevents duplicate active sessions.</p>
          <div className="state-list" aria-label="Supported examination session states">
            {sessionStates.map((state) => (
              <span key={state}>{state.replaceAll("_", " ")}</span>
            ))}
          </div>
        </article>

        <article className="card">
          <span className="badge">API-first Boundary</span>
          <h2>Backend endpoints now own identity workflows</h2>
          <p>
            Authentication, refresh tokens, role checks, candidates, exams, assignments and session transitions are exposed through
            FastAPI route groups for future secure exam-player integration.
          </p>
        </article>
      </section>
    </main>
  );
}
