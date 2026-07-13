"use client";

import { FormEvent, useState } from "react";
import { fetchCurrentUser, login } from "../../lib/api";

const roleDestinations: Record<string, string> = {
  Candidate: "/candidate",
  "Reviewer/Proctor": "/reviewer",
  Administrator: "/admin",
  "System Administrator": "/system-admin",
};

function destinationFor(roles: string[]): string {
  for (const role of ["System Administrator", "Administrator", "Reviewer/Proctor", "Candidate"]) {
    if (roles.includes(role)) {
      return roleDestinations[role];
    }
  }
  return "/";
}

export default function LoginPage() {
  const [email, setEmail] = useState("admin@miva.edu.ng");
  const [institutionCode, setInstitutionCode] = useState("MIVA");
  const [password, setPassword] = useState("");
  const [status, setStatus] = useState<string>("Use a seeded local demo account or an account created by a System Administrator.");
  const [busy, setBusy] = useState(false);

  async function onSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setStatus("Authenticating against FastAPI...");
    try {
      const tokens = await login({ email, password, institution_code: institutionCode || undefined });
      sessionStorage.setItem("serps_access_token", tokens.access_token);
      sessionStorage.setItem("serps_refresh_token", tokens.refresh_token);
      const user = await fetchCurrentUser(tokens.access_token);
      sessionStorage.setItem("serps_current_user", JSON.stringify(user));
      window.location.href = destinationFor(user.roles);
    } catch (error) {
      setStatus(error instanceof Error ? error.message : "Login failed.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main className="page-shell compact-shell">
      <section className="auth-layout">
        <div className="hero auth-hero">
          <p className="eyebrow">SERPS POP</p>
          <h1>Sign in to the prototype dashboard</h1>
          <p>
            Authentication is handled by the FastAPI Sprint 2 identity foundation. Roles are read from authenticated backend claims,
            not from a Streamlit-style role simulator.
          </p>
        </div>

        <form className="card auth-card" onSubmit={onSubmit}>
          <span className="badge">Authentication</span>
          <h2>Login</h2>
          <label>
            Institution code
            <input value={institutionCode} onChange={(event) => setInstitutionCode(event.target.value)} />
          </label>
          <label>
            Email
            <input type="email" value={email} onChange={(event) => setEmail(event.target.value)} />
          </label>
          <label>
            Password
            <input type="password" value={password} onChange={(event) => setPassword(event.target.value)} required />
          </label>
          <button type="submit" disabled={busy}>{busy ? "Signing in..." : "Sign in"}</button>
          <p className="form-note">{status}</p>
          <p className="form-note">
            Password reset and hardened cookie-backed browser sessions are planned production upgrades. This POP page uses short-lived
            API tokens for local development validation.
          </p>
        </form>
      </section>
    </main>
  );
}
