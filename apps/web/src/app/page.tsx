import { HealthCard } from "../components/HealthCard";

const modules = [
  "Candidate Portal",
  "Reviewer / Proctor Portal",
  "Administrator Portal",
  "Structured Evidence API",
  "Contextual Intelligence Engine",
  "Institutional Policy Workflow",
];

export default function HomePage() {
  return (
    <main className="page-shell">
      <section className="hero" aria-labelledby="hero-title">
        <p className="eyebrow">SERPS POP</p>
        <h1 id="hero-title">Secure Explainable Remote Proctoring System</h1>
        <p>
          Production-oriented prototype foundation preserving the validated SERPS governance pipeline while separating frontend, API, persistence and domain logic.
        </p>
      </section>

      <section className="status-grid" aria-label="SERPS POP foundation status">
        <HealthCard />
        {modules.map((module) => (
          <article className="card" key={module}>
            <span className="badge">Foundation</span>
            <h2>{module}</h2>
            <p>Scaffolded for controlled migration from the validated SERPS POC.</p>
          </article>
        ))}
      </section>
    </main>
  );
}
