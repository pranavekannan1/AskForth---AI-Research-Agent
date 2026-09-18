"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { onAuthStateChanged } from "firebase/auth";

import { auth, authPersistence } from "@/lib/firebase";

export default function HomePage() {
  const router = useRouter();

  useEffect(() => {
    let mounted = true;
    let unsubscribe: (() => void) | undefined;

    authPersistence
      .then(() => {
        if (!mounted) return;
        unsubscribe = onAuthStateChanged(auth, (user) => {
          if (!mounted) return;
              router.replace(user ? "/research" : "/login");
        });
      })
      .catch(() => {
            if (mounted) router.replace("/login");
      });

    return () => {
      mounted = false;
      unsubscribe?.();
    };
  }, [router]);

  return (
    <main className="landing-page">
      <div className="landing-content">
        <div className="landing-logo">✦</div>
        <p>Initialising AskForth…</p>
      </div>
    </main>
  );
}
