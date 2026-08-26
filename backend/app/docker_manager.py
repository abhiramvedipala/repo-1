"""Docker orchestration for Phase 2: one code-server container per active
lab session, network-isolated from the outside world except for an
allowlisted egress proxy (PyPI/npm only).

Design notes (verified by hand against a real Docker daemon before writing
this, not assumed):
  - Session containers attach ONLY to `lab-internal`, a Docker network
    created with internal=True. Docker refuses that network any default
    route out, so a session container has no way to reach the internet
    except through whatever else is on that same network.
  - `lab-egress-proxy` (tinyproxy) is the only container attached to BOTH
    lab-internal and lab-external (external has normal outbound access).
    Session containers get HTTP_PROXY/HTTPS_PROXY pointed at it, and
    tinyproxy's filter.list only allows CONNECT to PyPI/npm hosts.
  - No host port is published for the session container. A container on
    an internal network is NOT reachable via `-p hostport:port` (verified:
    published ports don't route through an internal network) — but the
    Docker bridge itself is still reachable from the host directly
    (verified), so the backend talks to the container at its own
    container_ip:8080 on the bridge instead of publishing anything.
"""
from __future__ import annotations

import json
import os
import secrets
import socket
import time
from pathlib import Path

import docker
from docker.errors import NotFound

from app.config import (
    DOCKER_DIR,
    LAB_CONTAINER_PORT,
    LAB_CONTAINER_PREFIX,
    LAB_CPU_LIMIT,
    LAB_MEM_LIMIT,
    LAB_IMAGE,
    LAB_NETWORK_EXTERNAL,
    LAB_NETWORK_INTERNAL,
    LAB_PROXY_CONTAINER_NAME,
    LAB_PROXY_IMAGE,
    LAB_PROXY_PORT,
    LAB_SESSION_MINUTES_DEFAULT,
    LAB_SESSION_MINUTES_MAX,
    REPO_ROOT,
)
from app import pylabs_bridge as pb


class LabError(Exception):
    """Raised for any container-orchestration failure the API should surface."""


# codercom/code-server always runs its process as this fixed uid/gid (the
# image's "coder" user) — not configurable per-container without losing the
# image's own baked-in HOME ownership. The workspace dir is bind-mounted
# from the host, where our backend (often root, e.g. in this dev setup)
# creates files as itself — so without this, code-server can read the
# learner's files but can't save edits back to them.
CODE_SERVER_UID = 1000
CODE_SERVER_GID = 1000


def sync_workspace_ownership(ws_dir: Path) -> None:
    """Best-effort chown of a workspace dir (+ contents) to match
    code-server's fixed user, so the container can actually write to it.
    Silently skipped if we don't have permission to chown (e.g. the
    backend itself runs as a non-root, non-matching user) — Docker's own
    user-namespace remapping is the right fix in that deployment shape,
    and failing lab start over this would be worse than a learner hitting
    a read-only file and asking about it.
    """
    try:
        for root, dirs, files in os.walk(ws_dir):
            os.chown(root, CODE_SERVER_UID, CODE_SERVER_GID)
            for f in files:
                os.chown(os.path.join(root, f), CODE_SERVER_UID, CODE_SERVER_GID)
    except (PermissionError, OSError):
        pass


_client: docker.DockerClient | None = None


def client() -> docker.DockerClient:
    global _client
    if _client is None:
        try:
            _client = docker.from_env()
            _client.ping()
        except Exception as e:
            raise LabError(
                "Docker is not reachable. Phase 2 needs a Docker daemon "
                f"(dockerd) running on this host. ({e})"
            ) from e
    return _client


# ── one-time setup: images + networks + proxy ──────────────────────────
def ensure_images() -> None:
    c = client()
    for image, build_dir in (
        (LAB_IMAGE, DOCKER_DIR / "lab-code-server"),
        (LAB_PROXY_IMAGE, DOCKER_DIR / "proxy"),
    ):
        try:
            c.images.get(image)
        except NotFound:
            c.images.build(path=str(build_dir), tag=image, rm=True)


def ensure_networks() -> None:
    c = client()
    for name, internal in ((LAB_NETWORK_INTERNAL, True), (LAB_NETWORK_EXTERNAL, False)):
        try:
            c.networks.get(name)
        except NotFound:
            c.networks.create(name, driver="bridge", internal=internal)


def ensure_proxy() -> None:
    c = client()
    ensure_networks()
    try:
        proxy = c.containers.get(LAB_PROXY_CONTAINER_NAME)
        if proxy.status != "running":
            proxy.start()
        return
    except NotFound:
        pass

    proxy = c.containers.run(
        LAB_PROXY_IMAGE,
        name=LAB_PROXY_CONTAINER_NAME,
        detach=True,
        network=LAB_NETWORK_EXTERNAL,
        restart_policy={"Name": "unless-stopped"},
    )
    c.networks.get(LAB_NETWORK_INTERNAL).connect(proxy)


def ensure_ready() -> None:
    """Call before touching sessions: images built, networks + proxy up."""
    ensure_images()
    ensure_proxy()


# ── session lifecycle ───────────────────────────────────────────────────
def _container_name(user_id: int) -> str:
    return f"{LAB_CONTAINER_PREFIX}{user_id}"


def _get_container(name: str):
    try:
        return client().containers.get(name)
    except NotFound:
        return None


def _container_ip(container) -> str | None:
    container.reload()
    networks = container.attrs.get("NetworkSettings", {}).get("Networks", {})
    net = networks.get(LAB_NETWORK_INTERNAL)
    return net["IPAddress"] if net else None


def clamp_minutes(minutes: int | None) -> int:
    m = minutes or LAB_SESSION_MINUTES_DEFAULT
    return max(1, min(m, LAB_SESSION_MINUTES_MAX))


def start_container(user_id: int, minutes: int | None = None) -> dict:
    """Idempotent: reuses a still-running, unexpired container if one
    exists for this user; otherwise removes any stale one and starts
    fresh. Returns the fields the LabSession row should be updated with.
    """
    ensure_ready()
    c = client()
    name = _container_name(user_id)

    existing = _get_container(name)
    if existing is not None:
        if existing.status == "running":
            ip = _container_ip(existing)
            if ip:
                return {"reused": True, "container_id": existing.id, "container_ip": ip}
        # stopped/dead/unhealthy — clear it and start clean
        existing.remove(force=True)

    ws_dir = pb.workspace_dir_for(user_id)
    pylabs_src = REPO_ROOT / "pylabs"
    check_runner = Path(__file__).resolve().parent.parent / "docker" / "check_runner.py"

    sync_workspace_ownership(ws_dir)

    container = c.containers.run(
        LAB_IMAGE,
        name=name,
        command=[
            "--auth", "none",
            "--disable-workspace-trust",  # skip the "trust this folder?" interstitial
            "--bind-addr", f"0.0.0.0:{LAB_CONTAINER_PORT}",
            "/home/coder/project",
        ],
        detach=True,
        network=LAB_NETWORK_INTERNAL,
        volumes={
            str(ws_dir): {"bind": "/home/coder/project", "mode": "rw"},
            str(pylabs_src): {"bind": "/opt/lab/pylabs", "mode": "ro"},
            str(check_runner): {"bind": "/opt/lab/check_runner.py", "mode": "ro"},
        },
        environment={
            "HTTP_PROXY": f"http://{LAB_PROXY_CONTAINER_NAME}:{LAB_PROXY_PORT}",
            "HTTPS_PROXY": f"http://{LAB_PROXY_CONTAINER_NAME}:{LAB_PROXY_PORT}",
            "NO_PROXY": "localhost,127.0.0.1",
            "TERM": "xterm-256color",
        },
        mem_limit=LAB_MEM_LIMIT,
        nano_cpus=int(LAB_CPU_LIMIT * 1_000_000_000),
        labels={"lab-platform": "session", "lab-user-id": str(user_id)},
    )

    # Wait for the container to get its IP AND for code-server to actually
    # be accepting connections — having an IP just means the network stack
    # is up, not that the process inside has bound its port yet. Without
    # this second check, a "start" call can return before the very first
    # proxied request would succeed (seen in practice: a fast page load
    # would hit the container a couple hundred ms too early and get a
    # connection-refused).
    ip = None
    for _ in range(30):
        container.reload()
        if container.status != "running":
            logs = container.logs(tail=50).decode(errors="replace")
            raise LabError(f"session container exited immediately:\n{logs}")
        ip = _container_ip(container)
        if ip:
            break
        time.sleep(0.2)
    if not ip:
        raise LabError("session container never got a network address")

    if not _wait_for_port(ip, LAB_CONTAINER_PORT, timeout=15):
        logs = container.logs(tail=50).decode(errors="replace")
        raise LabError(f"code-server did not start accepting connections in time:\n{logs}")

    return {"reused": False, "container_id": container.id, "container_ip": ip}


def _wait_for_port(host: str, port: int, timeout: float) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with socket.create_connection((host, port), timeout=1):
                return True
        except OSError:
            time.sleep(0.2)
    return False


def stop_container(user_id: int) -> None:
    name = _container_name(user_id)
    existing = _get_container(name)
    if existing is not None:
        existing.remove(force=True)


def container_running(container_id: str | None) -> bool:
    if not container_id:
        return False
    try:
        c = client().containers.get(container_id)
        return c.status == "running"
    except NotFound:
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(24)


def run_check(container_id: str, task_id: str) -> dict:
    """docker exec the check runner inside a running session container."""
    try:
        c = client().containers.get(container_id)
    except NotFound as e:
        raise LabError("session container is gone — restart the lab") from e

    if c.status != "running":
        raise LabError("session container is not running — restart the lab")

    exit_code, output = c.exec_run(
        ["python3", "/opt/lab/check_runner.py", task_id, "/home/coder/project", "/opt/lab"],
        demux=False,
    )
    text = output.decode(errors="replace") if output else ""
    if exit_code != 0 and not text.strip():
        raise LabError(f"check runner failed (exit {exit_code}) with no output")

    try:
        # check_runner.py prints exactly one JSON line; be lenient about
        # any stray output before it (e.g. a slow shell profile echo).
        line = text.strip().splitlines()[-1]
        return json.loads(line)
    except Exception as e:
        raise LabError(f"could not parse check output: {text!r}") from e
