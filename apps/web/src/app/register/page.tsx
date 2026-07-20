"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { registerCandidate } from "../../lib/api";

export default function CandidateRegistrationPage() {
  const [status, setStatus] = useState("Create a candidate account using an active institution code.");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    const form = new FormData(event.currentTarget);
    try {
      await registerCandidate({
        institution_code: String(form.get("institution_code")),
        candidate_identifier: String(form.get("candidate_identifier")),
        full_name: String(form.get("full_name")),
        email: String(form.get("email")),
        password: String(form.get("password")),
      });
      setStatus("Registration complete. You can now sign in with the candidate account.");
      event.currentTarget.reset();
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Registration failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page-shell compact-shell">
      <section className="auth-layout">
        <div className="hero auth-hero">
          <p className="eyebrow">SERPS Candidate Journey</p>
          <h1>Register for assigned examinations</h1>
          <p>Registration creates an institution-scoped candidate account. Consent and device checks follow after authentication.</p>
          <Link className="hero-link" href="/login">Already registered? Sign in</Link>
        </div>
        <form className="card auth-card" onSubmit={submit}>
          <span className="badge">Candidate Registration</span>
          <label>Institution code<input name="institution_code" required /></label>
          <label>Candidate identifier<input name="candidate_identifier" required /></label>
          <label>Full name<input name="full_name" required /></label>
          <label>Email<input name="email" type="email" required /></label>
          <label>Password<input name="password" type="password" minLength={8} required /></label>
          <button type="submit" disabled={busy}>{busy ? "Registering..." : "Register"}</button>
          <p className="form-note">{status}</p>
        </form>
      </section>
    </main>
  );
}
