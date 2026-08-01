"use client";

import { useEffect } from "react";

export default function GlobalErrorBoundary({ error, reset }: { error: Error & { digest?: string }; reset: () => void }) {
  useEffect(() => { console.error("SERPS route error", { digest: error.digest, name: error.name }); }, [error]);
  return <main className="page-shell"><section className="card state-card" role="alert"><span className="badge">Unable to display this screen</span><h1>A recoverable application error occurred</h1><p>The rest of SERPS remains available. Retry this screen; if the issue continues, provide support reference <strong>{error.digest ?? "SERPS-CLIENT"}</strong>.</p><button type="button" onClick={reset}>Retry screen</button></section></main>;
}
