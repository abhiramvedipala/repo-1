"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";

export default function SignupPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      await api.signup(email, password);
      router.push("/lab");
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "sign up failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-bg">
      <form
        onSubmit={onSubmit}
        className="w-full max-w-sm bg-bg-panel border border-bg-border rounded-xl p-8 shadow-xl"
      >
        <div className="mb-6 text-center">
          <div className="text-lg font-semibold tracking-tight">
            <span className="text-accent">Lab</span> Platform
          </div>
          <div className="text-text-dim text-sm mt-1">
            Create an account — same 21 tasks, your own isolated labs
          </div>
        </div>

        <label className="block text-sm text-text-dim mb-1">Email</label>
        <input
          type="email"
          required
          value={email}
          onChange={(e) => setEmail(e.target.value)}
          className="w-full mb-4 rounded-md bg-bg-raised border border-bg-border px-3 py-2 text-sm outline-none focus:border-accent"
          placeholder="you@example.com"
        />

        <label className="block text-sm text-text-dim mb-1">Password</label>
        <input
          type="password"
          required
          minLength={8}
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full mb-1 rounded-md bg-bg-raised border border-bg-border px-3 py-2 text-sm outline-none focus:border-accent"
          placeholder="••••••••"
        />
        <div className="text-xs text-text-faint mb-4">At least 8 characters.</div>

        {error && <div className="mb-4 text-sm text-fail">{error}</div>}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-accent hover:bg-accent-hover disabled:opacity-60 transition-colors py-2 text-sm font-medium"
        >
          {loading ? "Creating account…" : "Create account"}
        </button>

        <div className="text-center text-xs text-text-faint mt-4">
          Already have an account?{" "}
          <a href="/login" className="text-accent hover:text-accent-hover">
            Sign in
          </a>
        </div>
      </form>
    </div>
  );
}
