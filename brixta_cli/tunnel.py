"""Secure local HTTPS tunnel lifecycle."""

from __future__ import annotations

from pathlib import Path
import queue
import re
import shutil
import subprocess
import threading
import time


TUNNEL_URL = re.compile(r"https://[a-z0-9-]+\.trycloudflare\.com")


def start_cloudflare_tunnel(local_url: str, log_path: Path) -> tuple[subprocess.Popen[str], str]:
    executable = shutil.which("cloudflared")
    if executable is None:
        raise RuntimeError(
            "cloudflared is required for --local. Install it with `brew install cloudflared` "
            "and run the command again."
        )
    process = subprocess.Popen(
        [executable, "tunnel", "--no-autoupdate", "--url", local_url],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        start_new_session=True,
    )
    lines: queue.Queue[str] = queue.Queue()

    def consume() -> None:
        assert process.stdout is not None
        with log_path.open("a", encoding="utf-8") as log:
            for line in process.stdout:
                log.write(line)
                log.flush()
                lines.put(line)

    threading.Thread(target=consume, daemon=True).start()
    deadline = time.monotonic() + 35
    while time.monotonic() < deadline:
        if process.poll() is not None:
            raise RuntimeError(f"cloudflared exited early; inspect {log_path}")
        try:
            line = lines.get(timeout=0.5)
        except queue.Empty:
            continue
        match = TUNNEL_URL.search(line)
        if match:
            return process, f"{match.group(0)}/mcp"
    process.terminate()
    raise RuntimeError(f"Timed out waiting for the tunnel URL; inspect {log_path}")
