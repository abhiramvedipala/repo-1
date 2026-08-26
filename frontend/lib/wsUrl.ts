import { backendOrigin } from "./backendUrl";

/** Where the terminal WebSocket connects. Single-host Phase 1: talk to the
 * backend directly (its session cookie is host-only, so it's sent to any
 * port on the same host — no proxy needed). Override for other setups.
 */
export function terminalWsUrl(): string {
  if (process.env.NEXT_PUBLIC_TERMINAL_WS_URL) {
    return process.env.NEXT_PUBLIC_TERMINAL_WS_URL;
  }
  const origin = backendOrigin();
  return origin.replace(/^http/, "ws") + "/ws/terminal";
}
