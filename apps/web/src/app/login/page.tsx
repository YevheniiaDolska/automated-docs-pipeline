"use client";

import { FormEvent, useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/api";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await auth.login({ email, password });
      router.push("/dashboard");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Login failed");
    } finally {
      setLoading(false);
    }
  }

  function startOAuth(provider: "google" | "github") {
    const override =
      provider === "google"
        ? process.env.NEXT_PUBLIC_OAUTH_GOOGLE_URL
        : process.env.NEXT_PUBLIC_OAUTH_GITHUB_URL;
    window.location.href = override || `/api/auth/oauth/${provider}`;
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-brand/5 to-brand-light/5">
      <div className="w-full max-w-sm rounded-xl bg-surface p-8 shadow-lg">
        <h1 className="text-center text-2xl font-extrabold text-brand">VeriDoc</h1>
        <p className="mt-1 text-center text-sm text-muted">Sign in to your account</p>

        {error && (
          <div className="mt-4 rounded border border-red-200 bg-red-50 p-3 text-sm text-red-700">
            {error}
          </div>
        )}

        <div className="mt-6 space-y-2">
          <button
            type="button"
            onClick={() => startOAuth("google")}
            className="w-full rounded-md border border-line bg-white py-2 text-sm font-semibold text-slate-800 hover:bg-slate-50"
          >
            Continue with Google
          </button>
          <button
            type="button"
            onClick={() => startOAuth("github")}
            className="w-full rounded-md border border-line bg-white py-2 text-sm font-semibold text-slate-800 hover:bg-slate-50"
          >
            Continue with GitHub
          </button>
        </div>

        <div className="mt-5 flex items-center gap-3 text-xs uppercase tracking-wide text-muted">
          <span className="h-px flex-1 bg-line" />
          <span>or</span>
          <span className="h-px flex-1 bg-line" />
        </div>

        <form onSubmit={handleSubmit} className="mt-5 space-y-4">
          <div>
            <label htmlFor="email" className="block text-sm font-medium">
              Email
            </label>
            <input
              id="email"
              type="email"
              required
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              placeholder="you@company.com"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium">
              Password
            </label>
            <input
              id="password"
              type="password"
              required
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="mt-1 w-full rounded-md border border-line px-3 py-2 text-sm focus:border-brand focus:outline-none focus:ring-1 focus:ring-brand"
              placeholder="********"
            />
          </div>
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-md bg-brand py-2 text-sm font-semibold text-white hover:bg-brand/90 disabled:opacity-50"
          >
            {loading ? "Signing in..." : "Sign in"}
          </button>
        </form>

        <p className="mt-6 text-center text-sm text-muted">
          No account?{" "}
          <Link href="/register" className="font-medium text-brand hover:underline">
            Sign up
          </Link>
        </p>
      </div>
    </div>
  );
}
