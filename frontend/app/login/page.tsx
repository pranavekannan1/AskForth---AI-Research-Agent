"use client";

import { FormEvent, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import {
  onAuthStateChanged,
  sendPasswordResetEmail,
  signInWithEmailAndPassword,
} from "firebase/auth";

import { auth, authPersistence } from "@/lib/firebase";
import { authenticatedFetch } from "@/lib/api";
import { getAuthErrorMessage } from "@/lib/auth-errors";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [forgotPassword, setForgotPassword] = useState(false);
  const [resetSent, setResetSent] = useState(false);

  useEffect(() => {
    let mounted = true;

    authPersistence.then(() => {
      if (!mounted) return;
      const unsubscribe = onAuthStateChanged(auth, (user) => {
        if (user) router.replace("/research");
        unsubscribe();
      });
    }).catch(() => undefined);

    return () => { mounted = false; };
  }, [router]);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await authPersistence;
      await signInWithEmailAndPassword(auth, email.trim(), password);
      await authenticatedFetch("/health");
      router.replace("/research");
    } catch (err) {
      setError(getAuthErrorMessage(err, "Unable to log in. Please try again."));
    } finally {
      setLoading(false);
    }
  }

  async function handleForgotPassword(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);

    try {
      await authPersistence;
      await sendPasswordResetEmail(auth, email.trim());
      setResetSent(true);
    } catch {
      setError("We could not send a reset email. Check your details and try again.");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">
      <div className="auth-card">
        <div className="auth-logo">✦</div>
        <h1>Welcome back</h1>
        <p className="auth-subtitle">
          {forgotPassword
            ? "Enter the email you used to register."
            : "Sign in to continue your AskForth workspace."}
        </p>

        {resetSent ? (
          <div className="auth-success">
            Check your email for a password reset link. It may take a few minutes to arrive.
          </div>
        ) : (
        <form className="auth-form" onSubmit={forgotPassword ? handleForgotPassword : handleLogin}>
          <div className="auth-field">
            <label htmlFor="email">Email</label>
            <input id="email" type="email" value={email} onChange={(e) => setEmail(e.target.value)} autoComplete="email" required />
          </div>
          {!forgotPassword && <div className="auth-field">
            <label htmlFor="password">Password</label>
            <input id="password" type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="current-password" required />
          </div>}
          {error && <div className="auth-error">{error}</div>}
          <button className="auth-button" disabled={loading}>
            {loading ? "Please wait…" : forgotPassword ? "Send reset email" : "Log in"}
          </button>
        </form>
        )}

        {!resetSent && !forgotPassword && (
          <button className="auth-link" onClick={() => { setForgotPassword(true); setError(""); }}>
            Forgot password?
          </button>
        )}
        {(forgotPassword || resetSent) && (
          <button className="auth-link" onClick={() => { setForgotPassword(false); setResetSent(false); setError(""); }}>
            Back to log in
          </button>
        )}

        <p className="auth-footer">
          Your account and research history are restored automatically on the next visit.
        </p>
        <p className="auth-footer">
          New to AskForth? <Link href="/sign-up">Create an account</Link>
        </p>
      </div>
    </main>
  );
}
