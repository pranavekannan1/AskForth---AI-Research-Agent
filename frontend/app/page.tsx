"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { onAuthStateChanged } from "firebase/auth";

import { auth, authPersistence } from "@/lib/firebase";

export default function HomePage() {
  const router = useRouter();
  const [checking, setChecking] = useState(true);

  useEffect(() => {
    let mounted = true;
    let unsubscribe: (() => void) | undefined;

    authPersistence
      .then(() => {
        if (!mounted) return;
        unsubscribe = onAuthStateChanged(auth, (user) => {
          if (!mounted) return;
          if (user) {
            router.replace("/research");
          } else {
            setChecking(false);
          }
        });
      })
      .catch(() => {
        if (mounted) setChecking(false);
      });

    return () => {
      mounted = false;
      unsubscribe?.();
    };
  }, [router]);

  if (checking) {
    return (
      <main className="landing-page">
        <div className="landing-content">
          <div className="landing-logo">✦</div>
          <p>Initialising AskForth…</p>
        </div>
      </main>
    );
  }

  return (
    <main className="landing-page">
      <div className="landing-content">
        <div className="landing-logo">✦</div>
        <div className="landing-kicker">AI RESEARCH AGENT</div>
        <h1>AskForth</h1>
        <p>
          A persistent research workspace that plans investigations, searches evidence,
          highlights uncertainty, and turns research into professional reports.
        </p>
        <div className="landing-actions">
          <Link href="/login">Log in</Link>
          <Link href="/sign-up">Create account</Link>
        </div>
      </div>
    </main>
  );
}
