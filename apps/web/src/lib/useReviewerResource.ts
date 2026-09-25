"use client";
import { useCallback, useEffect, useRef, useState } from "react";

/** Preserve the rendered review during refresh; only the latest request may publish. */
export function useReviewerResource<T>(key: string, fetcher: (key: string, signal: AbortSignal) => Promise<T>) {
  const [view, setView] = useState<{ key: string; data: T | null; error: string; pending: boolean; updatedAt: string | null }>({ key, data: null, error: "", pending: true, updatedAt: null });
  const active = useRef<{ id: number; key: string; controller: AbortController } | null>(null);
  const sequence = useRef(0);
  const refresh = useCallback(async (background = false) => {
    if (background && active.current?.key === key) return;
    active.current?.controller.abort();
    const request = { id: ++sequence.current, key, controller: new AbortController() };
    active.current = request;
    await Promise.resolve();
    if (active.current !== request) return;
    setView((previous) => ({ key, data: previous.key === key ? previous.data : null, error: "", pending: true, updatedAt: previous.key === key ? previous.updatedAt : null }));
    try {
      const data = await fetcher(key, request.controller.signal);
      if (active.current === request) setView({ key, data, error: "", pending: false, updatedAt: new Date().toISOString() });
    } catch (error) {
      if (active.current === request && !request.controller.signal.aborted) setView((previous) => ({ ...previous, pending: false, error: error instanceof Error ? error.message : "Reviewer data unavailable." }));
    } finally { if (active.current === request) active.current = null; }
  }, [key, fetcher]);
  useEffect(() => {
    const initial = window.setTimeout(() => void refresh(), 0);
    const poll = window.setInterval(() => void refresh(true), 10000);
    return () => { window.clearTimeout(initial); window.clearInterval(poll); active.current?.controller.abort(); active.current = null; };
  }, [refresh]);
  return { data: view.key === key ? view.data : null, error: view.key === key ? view.error : "", pending: view.key !== key || view.pending, updatedAt: view.key === key ? view.updatedAt : null, refresh };
}

export function reviewerFilter(query: string, name: string, value: string): string {
  const params = new URLSearchParams(query);
  if (value) params.set(name, value); else params.delete(name);
  return params.toString();
}
