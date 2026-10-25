import { useEffect, useState } from "react";

const SLOW_MS = 3000;

/** Loading placeholder; after 3 s it explains that a free-plan server may be starting up. */
export function Skeleton({ label }: { label: string }) {
  const [slow, setSlow] = useState(false);
  useEffect(() => {
    const timer = setTimeout(() => setSlow(true), SLOW_MS);
    return () => clearTimeout(timer);
  }, []);
  return (
    <div className="skeleton" role="status" aria-label={label}>
      {slow && <p className="muted">Waking up the server, this can take a few seconds on the free plan…</p>}
    </div>
  );
}
