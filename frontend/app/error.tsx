"use client";

import Link from "next/link";

export default function Error({
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  return (
    <main className="error-page">
      <div className="error-card">
        <div className="landing-logo">!</div>
        <p className="landing-kicker">ASKFORTH</p>
        <h1>We couldn&apos;t load this workspace.</h1>
        <p>Something interrupted the page. Try loading it again, or return to the start.</p>
        <div className="landing-actions">
          <button type="button" onClick={reset}>Try again</button>
          <Link href="/">Back to start</Link>
        </div>
      </div>
    </main>
  );
}