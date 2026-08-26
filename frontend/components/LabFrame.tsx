"use client";

import { backendOrigin } from "@/lib/backendUrl";

export default function LabFrame({ proxyUrl }: { proxyUrl: string }) {
  const src = `${backendOrigin()}${proxyUrl}`;
  // Deliberately unsandboxed: this iframe is our own backend proxying our
  // own container for the same authenticated user (not third-party
  // content), and VS Code Web needs a wide set of capabilities — clipboard,
  // downloads, its own nested extension-host iframe, popups for opened
  // links — that a hand-tuned sandbox allowlist risks silently breaking.
  return <iframe src={src} title="Lab environment" className="w-full h-full border-0 bg-white" />;
}
