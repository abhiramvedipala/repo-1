/** The backend's own origin, for things Next's /api/* rewrite doesn't cover
 * (WebSocket upgrades, and the code-server iframe's own many sub-requests
 * incl. its internal websockets) — see terminal WS for why this bypasses
 * the rewrite proxy. The session cookie is host-only, so it's sent here
 * too regardless of port.
 */
export function backendOrigin(): string {
  if (process.env.NEXT_PUBLIC_BACKEND_ORIGIN) {
    return process.env.NEXT_PUBLIC_BACKEND_ORIGIN;
  }
  if (typeof window === "undefined") return "";
  const port = process.env.NEXT_PUBLIC_BACKEND_PORT || "8000";
  return `${window.location.protocol}//${window.location.hostname}:${port}`;
}
