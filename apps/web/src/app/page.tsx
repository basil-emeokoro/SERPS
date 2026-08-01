import Link from "next/link";
import { HealthCard } from "../components/HealthCard";

const governancePipeline = [
  {
    title: "Structured Evidence",
    purpose: "Creates durable, time-stamped records from candidate, browser and camera activity.",
    workflow: "Candidate activity is validated, linked to the correct session and stored as an EvidenceEvent.",
    role: "Provides the traceable factual input used by the reasoning and review stages.",
    governance: "Evidence is never treated as a misconduct decision; provenance and ownership remain explicit.",
  },
  {
    title: "Contextual Intelligence Engine",
    purpose: "Interprets related evidence within the current examination context.",
    workflow: "Bounded rules evaluate event type, recency, recurrence and camera context to produce an explainable risk assessment.",
    role: "Transforms isolated observations into a structured risk level, score, confidence and explanation.",
    governance: "Every assessment retains the contributing evidence identifiers and rule version for auditability.",
  },
  {
    title: "Agentic Recommendation",
    purpose: "Suggests a proportionate operational response to the current assessment.",
    workflow: "The recommendation service maps the assessment to a bounded action and records its rationale.",
    role: "Supports reviewers with consistent decision guidance without replacing professional judgement.",
    governance: "Recommendations are advisory and cannot independently penalise a candidate or terminate an examination.",
  },
  {
    title: "Institutional Policy",
    purpose: "Applies institution-defined governance constraints to the recommendation.",
    workflow: "The policy evaluator records the applicable policy version, threshold and required human action.",
    role: "Keeps operational responses aligned with institutional rules rather than hidden application behaviour.",
    governance: "Policy outcomes are persisted and prohibit automatic misconduct determinations in this prototype.",
  },
  {
    title: "Human Review",
    purpose: "Places final operational authority with an authorised reviewer or proctor.",
    workflow: "The reviewer inspects evidence, explanations and policy outcomes before recording an action and rationale.",
    role: "Provides accountable human oversight for consequential examination decisions.",
    governance: "Decisions are append-only, institution-scoped and included in the audit timeline and report.",
  },
];

const portalPanels = [
  {
    title: "Administrator Portal",
    badge: "Administrator",
    href: "/admin",
    summary: "Inspect institution-scoped metrics, audit activity and dual-camera session metadata.",
    items: ["Operational metrics", "Risk distribution", "Dual-camera oversight", "Audit visibility"],
  },
  {
    title: "Reviewer / Proctor Portal",
    badge: "Reviewer",
    href: "/reviewer",
    summary: "Review evidence, explainable risk and policy outcomes before recording a human decision.",
    items: ["Session review queue", "Dual-camera metadata", "Reasoning timeline", "Recorded reviewer rationale"],
  },
  {
    title: "Candidate Portal",
    badge: "Candidate",
    href: "/candidate",
    summary: "Complete consent and dual-camera readiness before entering the bounded assessment demonstration workspace.",
    items: ["Consent and device checks", "Two distinct cameras", "Demonstration workspace", "Browser evidence events"],
  },
];

const sessionStates = ["authentication pending", "device check pending", "ready", "active", "paused", "completed", "terminated"];

export default function HomePage() {
  return (
    <main className="page-shell landing-shell">
      <section className="hero" aria-labelledby="hero-title">
        <p className="eyebrow">SERPS POP</p>
        <h1 id="hero-title">Secure Explainable Remote Proctoring System</h1>
        <p>
          A research prototype for explainable identity assurance, examination monitoring and human-governed review,
          designed to integrate with existing assessment systems.
        </p>
        <div className="hero-actions">
          <Link className="hero-link" href="/login">Sign in to SERPS</Link>
          <a className="hero-link secondary" href="#system-overview">Explore the system</a>
        </div>
      </section>

      <section id="system-overview" className="status-grid anchored-section" aria-label="SERPS system overview">
        <HealthCard />
        {portalPanels.map((panel) => (
          <Link className="portal-card-link" href={panel.href} key={panel.title} aria-label={`Open ${panel.title}`}>
            <article className="card portal-card">
              <span className="badge">{panel.badge}</span>
              <h2>{panel.title}</h2>
              <p>{panel.summary}</p>
              <ul>{panel.items.map((item) => <li key={item}>{item}</li>)}</ul>
              <span className="card-action">Open portal <span aria-hidden="true">→</span></span>
            </article>
          </Link>
        ))}
      </section>

      <section id="architecture" className="section-card anchored-section" aria-labelledby="pipeline-title">
        <div>
          <span className="badge">Explainable Governance Pipeline</span>
          <h2 id="pipeline-title">Evidence supports accountable, human-controlled decisions</h2>
          <p>
            Select each stage to see how SERPS converts structured observations into explainable, policy-aware review
            while preserving human authority.
          </p>
        </div>
        <div className="pipeline" aria-label="Interactive governance stages">
          {governancePipeline.map((step, index) => (
            <details className="governance-step" key={step.title} open={index === 0}>
              <summary><span>{String(index + 1).padStart(2, "0")}</span>{step.title}</summary>
              <div className="governance-step-content">
                <p><strong>Purpose:</strong> {step.purpose}</p>
                <p><strong>Workflow:</strong> {step.workflow}</p>
                <p><strong>Role in SERPS:</strong> {step.role}</p>
                <p><strong>Governance:</strong> {step.governance}</p>
              </div>
            </details>
          ))}
        </div>
      </section>

      <section className="two-column anchored-section" id="about">
        <article className="card">
          <span className="badge">Demonstration Workspace</span>
          <h2>Controlled monitored-session lifecycle</h2>
          <p>The bounded question workspace generates realistic browser events. It is not a complete CBT platform or secure browser.</p>
          <div className="state-list" aria-label="Supported examination session states">
            {sessionStates.map((state) => <span key={state}>{state}</span>)}
          </div>
        </article>

        <article className="card">
          <span className="badge">Dual-camera boundary</span>
          <h2>Local previews and privacy-conscious metadata</h2>
          <p>
            Candidate-facing and environmental cameras are acquired locally where hardware permits. SERPS records connection evidence
            and operational metadata, not raw video, and does not claim remote reviewer streaming.
          </p>
        </article>
      </section>

      <section id="documentation" className="two-column anchored-section">
        <article className="card">
          <span className="badge">Documentation</span>
          <h2>Demonstration and defence guidance</h2>
          <p>Installation, user, demonstration, security and limitations guides are maintained in the repository documentation package.</p>
          <Link className="button-link" href="/login">Begin the guided demonstration</Link>
        </article>
        <article id="version" className="card">
          <span className="badge">Version Information</span>
          <h2>Research Prototype Version 1.0 RC1</h2>
          <p>Environment validation remains conditional on PostgreSQL and physical dual-camera evidence. SERPS is not production-certified.</p>
        </article>
      </section>
    </main>
  );
}
