"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { api, ApiError } from "@/lib/api";

export default function LoginPage() {
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
      await api.login(email, password);
      router.push("/lab");
      router.refresh();
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "login failed");
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
          <div className="text-text-dim text-sm mt-1">Sign in to continue your labs</div>
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
          value={password}
          onChange={(e) => setPassword(e.target.value)}
          className="w-full mb-4 rounded-md bg-bg-raised border border-bg-border px-3 py-2 text-sm outline-none focus:border-accent"
          placeholder="••••••••"
        />

        {error && <div className="mb-4 text-sm text-fail">{error}</div>}

        <button
          type="submit"
          disabled={loading}
          className="w-full rounded-md bg-accent hover:bg-accent-hover disabled:opacity-60 transition-colors py-2 text-sm font-medium"
        >
          {loading ? "Signing in…" : "Sign in"}
        </button>
      </form>
    </div>
  );
}
