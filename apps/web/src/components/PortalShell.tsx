"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import type { MeResponse } from "../lib/api";
import { fetchCurrentUser, SessionExpiredError } from "../lib/api";
import { LoadingState } from "./OperationalStates";
import { RoleNavigation } from "./RoleNavigation";

type PortalShellProps = {
  allowedRoles: string[];
  title: string;
  badge: string;
  summary: string;
  children: React.ReactNode;
};

export function PortalShell({ allowedRoles, title, badge, summary, children }: PortalShellProps) {
  const [user, setUser] = useState<MeResponse | null>(null);
  const [loaded, setLoaded] = useState(false);
  const [expired, setExpired] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    async function initialise() {
      await Promise.resolve();
      const stored = sessionStorage.getItem("serps_current_user");
      const token = sessionStorage.getItem("serps_access_token");
      if (stored) {
        try { setUser(JSON.parse(stored) as MeResponse); }
        catch { sessionStorage.removeItem("serps_current_user"); }
      }
      if (!token) { setLoaded(true); return; }
      try {
        const current = await fetchCurrentUser(token, controller.signal);
        setUser(current);
        sessionStorage.setItem("serps_current_user", JSON.stringify(current));
      } catch (error) {
        if (error instanceof SessionExpiredError) setExpired(true);
      } finally { setLoaded(true); }
    }
    void initialise();
    return () => controller.abort();
  }, []);

  if (!loaded) {
    return <main className="page-shell"><LoadingState label="Validating portal session..." /></main>;
  }

  if (expired) return <main className="page-shell compact-shell"><section className="card empty-state" role="alert"><span className="badge">Session expired</span><h1>{title}</h1><p>Your authenticated session expired. Sign in again to continue.</p><Link className="button-link" href="/login">Return to login</Link></section></main>;

  if (!user) {
    return (
      <main className="page-shell compact-shell">
        <section className="card empty-state">
          <span className="badge">Authentication Required</span>
          <h1>{title}</h1>
          <p>Sign in before opening this role-aware portal.</p>
          <Link className="button-link" href="/login">Go to login</Link>
        </section>
      </main>
    );
  }

  const authorised = user.roles.some((role) => allowedRoles.includes(role));
  if (!authorised) {
    return (
      <main className="page-shell compact-shell">
        <section className="card empty-state">
          <span className="badge">Forbidden</span>
          <h1>{title}</h1>
          <p>{user.full_name} is signed in, but does not have access to this portal.</p>
          <p className="form-note">Current roles: {user.roles.join(", ")}</p>
          <Link className="button-link" href="/">Return home</Link>
        </section>
      </main>
    );
  }

  return (
    <main className="page-shell">
      <section className="portal-header">
        <div>
          <span className="badge">{badge}</span>
          <h1>{title}</h1>
          <p>{summary}</p>
        </div>
        <div className="signed-in-card">
          <strong>{user.full_name}</strong>
          <span>{user.email}</span>
          <span>{user.roles.join(", ")}</span>
        </div>
      </section>
      <RoleNavigation user={user} />
      {children}
    </main>
  );
}
