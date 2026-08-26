"use client";

import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { AdminStats, UserOut } from "@/lib/types";

const POLL_MS = 8_000;

function formatDuration(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}m ${s.toString().padStart(2, "0")}s`;
}

export default function AdminPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserOut | null>(null);
  const [checked, setChecked] = useState(false);
  const [stats, setStats] = useState<AdminStats | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    api
      .me()
      .then((u) => {
        setUser(u);
        if (!u.is_admin) router.push("/lab");
      })
      .catch(() => router.push("/login"))
      .finally(() => setChecked(true));
  }, [router]);

  const refresh = useCallback(() => {
    api
      .adminStats()
      .then(setStats)
      .catch((e) => setError(e.message ?? "failed to load stats"));
  }, []);

  useEffect(() => {
    if (!user?.is_admin) return;
    refresh();
    const t = setInterval(refresh, POLL_MS);
    return () => clearInterval(t);
  }, [user, refresh]);

  if (!checked || !user?.is_admin) {
    return <div className="min-h-screen flex items-center justify-center text-text-dim">Loading…</div>;
  }

  return (
    <div className="min-h-screen bg-bg text-text p-6 max-w-4xl mx-auto">
      <div className="flex items-center justify-between mb-6">
        <h1 className="text-xl font-semibold">Admin</h1>
        <a href="/lab" className="text-sm text-accent hover:text-accent-hover">
          ← Back to labs
        </a>
      </div>

      {error && <div className="text-fail text-sm mb-4">{error}</div>}

      {stats && (
        <>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-8">
            <StatTile label="Total users" value={stats.totalUsers} />
            <StatTile
              label="Active containers"
              value={`${stats.runningCount} / ${stats.maxConcurrentSessions}`}
              accent={stats.runningCount >= stats.maxConcurrentSessions ? "fail" : "pass"}
            />
            <StatTile label="In queue" value={stats.queuedCount} accent={stats.queuedCount > 0 ? "accent" : undefined} />
            <StatTile label="Capacity" value={stats.maxConcurrentSessions} />
          </div>

          <div className="mb-8">
            <h2 className="text-sm font-semibold text-text-dim uppercase tracking-wide mb-2">
              Running sessions ({stats.running.length})
            </h2>
            {stats.running.length === 0 ? (
              <div className="text-text-faint text-sm italic">No active lab sessions.</div>
            ) : (
              <div className="border border-bg-border rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-bg-panel text-text-faint text-xs uppercase">
                    <tr>
                      <th className="text-left px-3 py-2 font-medium">User</th>
                      <th className="text-left px-3 py-2 font-medium">Container</th>
                      <th className="text-left px-3 py-2 font-medium">Time left</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.running.map((s, i) => (
                      <tr key={i} className="border-t border-bg-border">
                        <td className="px-3 py-2">{s.userEmail}</td>
                        <td className="px-3 py-2 font-mono text-xs text-text-dim">{s.containerName}</td>
                        <td className="px-3 py-2">{formatDuration(s.remainingSeconds)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          <div>
            <h2 className="text-sm font-semibold text-text-dim uppercase tracking-wide mb-2">
              Queue ({stats.queued.length})
            </h2>
            {stats.queued.length === 0 ? (
              <div className="text-text-faint text-sm italic">Nobody's waiting.</div>
            ) : (
              <div className="border border-bg-border rounded-lg overflow-hidden">
                <table className="w-full text-sm">
                  <thead className="bg-bg-panel text-text-faint text-xs uppercase">
                    <tr>
                      <th className="text-left px-3 py-2 font-medium">User</th>
                      <th className="text-left px-3 py-2 font-medium">Waiting for</th>
                      <th className="text-left px-3 py-2 font-medium">Requested</th>
                    </tr>
                  </thead>
                  <tbody>
                    {stats.queued.map((s, i) => (
                      <tr key={i} className="border-t border-bg-border">
                        <td className="px-3 py-2">{s.userEmail}</td>
                        <td className="px-3 py-2">{formatDuration(s.queuedForSeconds)}</td>
                        <td className="px-3 py-2 text-text-dim">
                          {s.requestedMinutes ? `${s.requestedMinutes} min` : "—"}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </>
      )}
    </div>
  );
}

function StatTile({
  label,
  value,
  accent,
}: {
  label: string;
  value: string | number;
  accent?: "pass" | "fail" | "accent";
}) {
  const color = accent === "pass" ? "text-pass" : accent === "fail" ? "text-fail" : accent === "accent" ? "text-accent" : "text-text";
  return (
    <div className="border border-bg-border rounded-lg p-4 bg-bg-panel">
      <div className="text-text-faint text-xs uppercase tracking-wide mb-1">{label}</div>
      <div className={`text-2xl font-semibold ${color}`}>{value}</div>
    </div>
  );
}
