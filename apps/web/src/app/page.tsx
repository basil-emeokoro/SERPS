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
    summary: "Inspect API-backed institution-scoped metrics, audit activity and dual-camera session metadata.",
    items: ["Operational metrics", "Risk distribution", "Dual-camera oversight", "Audit visibility"],
  },
  {
    title: "Reviewer / Proctor Portal",
    badge: "Reviewer",
    href: "/reviewer",
    summary: "Review evidence, explainable risk, policy outcomes and both camera roles before recording a human decision.",
    items: ["API-backed session queue", "Dual-camera metadata", "CIE/IPIME timeline", "Immutable reviewer rationale"],
  },
  {
    title: "Candidate Portal",
    badge: "Candidate",
    href: "/candidate",
    summary: "Complete mandatory dual-camera readiness and enter the bounded assessment demonstration harness.",
    items: ["Consent and device checks", "Two distinct cameras", "Sample-question workspace", "Real browser evidence events"],
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
          Production-Oriented Prototype — Operational Early Alpha. SERPS is an explainable identity-assurance, monitoring and
          governance layer designed to integrate with external assessment systems.
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
            <Link className="button-link" href={panel.href}>Open operational portal</Link>
          </article>
        ))}
      </section>

      <section className="section-card" aria-labelledby="pipeline-title">
        <div>
          <span className="badge">Frozen Governance Pipeline</span>
          <h2 id="pipeline-title">Role-aware workflows still route through SERPS reasoning controls</h2>
          <p>
            Sprint 3D exposes the Sprint 3A–3C services through operational portals without moving governance authority into the
            frontend. Evidence informs explainable recommendations; human reviewers remain responsible for final actions.
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
          <span className="badge">Demonstration Workspace</span>
          <h2>Controlled monitored-session lifecycle</h2>
          <p>The bounded question workspace generates realistic browser events. It is not a full CBT platform or secure browser.</p>
          <div className="state-list" aria-label="Supported examination session states">
            {sessionStates.map((state) => (
              <span key={state}>{state.replaceAll("_", " ")}</span>
            ))}
          </div>
        </article>

        <article className="card">
          <span className="badge">Honest dual-camera boundary</span>
          <h2>Local previews, persisted operational metadata</h2>
          <p>
            Candidate-facing and environmental cameras are acquired locally where hardware permits. SERPS records connection evidence
            and privacy-safe metadata, not raw video, and does not claim enterprise remote streaming.
          </p>
        </article>
      </section>
    </main>
  );
}
