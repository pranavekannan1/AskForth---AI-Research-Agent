"use client";

import {
  FormEvent,
  useState,
} from "react";

import { useRouter } from "next/navigation";
import Link from "next/link";

import {
  createUserWithEmailAndPassword,
} from "firebase/auth";

import {
  auth,
  authPersistence,
} from "@/lib/firebase";
import { getAuthErrorMessage } from "@/lib/auth-errors";

export default function SignUpPage() {
  const router = useRouter();

  const [email, setEmail] =
    useState("");

  const [password, setPassword] =
    useState("");

  const [confirmPassword, setConfirmPassword] =
    useState("");

  const [loading, setLoading] =
    useState(false);

  const [error, setError] =
    useState("");

  async function handleSignUp(
    e: FormEvent<HTMLFormElement>
  ) {
    e.preventDefault();

    setError("");

    if (
      password !== confirmPassword
    ) {
      setError(
        "Passwords do not match."
      );
      return;
    }

    if (password.length < 6) {
      setError(
        "Password must contain at least 6 characters."
      );
      return;
    }

    setLoading(true);

    try {
      await authPersistence;

      await createUserWithEmailAndPassword(
        auth,
        email.trim(),
        password
      );

      /*
       * Firebase automatically keeps this
       * newly registered user authenticated.
       */
      router.replace("/research");
    } catch (err: unknown) {
      setError(getAuthErrorMessage(err, "Unable to create account. Please try again."));
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="auth-page">

      <div className="auth-card">

        <div className="auth-logo">
          ✦
        </div>

        <h1>
          Create your ResearchOS
          account
        </h1>

        <p className="auth-subtitle">
          Start building evidence-based
          research reports.
        </p>

        <form
          onSubmit={handleSignUp}
          className="auth-form"
        >

          <div className="auth-field">

            <label>
              Email
            </label>

            <input
              type="email"
              value={email}
              onChange={(e) =>
                setEmail(
                  e.target.value
                )
              }
              placeholder="you@example.com"
              autoComplete="email"
              required
            />

          </div>

          <div className="auth-field">

            <label>
              Password
            </label>

            <input
              type="password"
              value={password}
              onChange={(e) =>
                setPassword(
                  e.target.value
                )
              }
              placeholder="At least 6 characters"
              autoComplete="new-password"
              required
            />

          </div>

          <div className="auth-field">

            <label>
              Confirm password
            </label>

            <input
              type="password"
              value={confirmPassword}
              onChange={(e) =>
                setConfirmPassword(
                  e.target.value
                )
              }
              placeholder="Repeat your password"
              autoComplete="new-password"
              required
            />

          </div>

          {error && (
            <div className="auth-error">
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            className="auth-button"
          >
            {loading
              ? "Creating account..."
              : "Create account"}
          </button>

        </form>

        <p className="auth-footer">
          Already have an account? <Link href="/login">Log in</Link>
        </p>

      </div>

    </main>
  );
}