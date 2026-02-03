from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from flask import Flask, render_template, request

app = Flask(__name__)

DOWNLOAD_ROOT = Path("/download")
SAFE_SUBDIR_RE = re.compile(r"^[a-zA-Z0-9._-]+(?:/[a-zA-Z0-9._-]+)*$")


def resolve_target_dir(subdir: str) -> Path:
    cleaned = (subdir or "").strip().strip("/")
    if not cleaned:
        return DOWNLOAD_ROOT
    if not SAFE_SUBDIR_RE.match(cleaned):
        raise ValueError("Subdirectory contains invalid characters.")
    target = (DOWNLOAD_ROOT / cleaned).resolve()
    if not str(target).startswith(str(DOWNLOAD_ROOT)):
        raise ValueError("Subdirectory escapes download root.")
    return target


@app.get("/")
def index():
    return render_template("index.html")


@app.post("/download")
def download():
    url = (request.form.get("url") or "").strip()
    subdir = (request.form.get("subdir") or "").strip()
    if not url:
        return render_template("index.html", error="URL is required.")

    try:
        target_dir = resolve_target_dir(subdir)
    except ValueError as exc:
        return render_template("index.html", error=str(exc))

    target_dir.mkdir(parents=True, exist_ok=True)
    output_template = str(target_dir / "%(title)s.%(ext)s")

    cmd = ["yt-dlp", "-N", "10", "-o", output_template, url]
    try:
        result = subprocess.run(
            cmd,
            text=True,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        return render_template(
            "index.html",
            error="yt-dlp is not available in the container.",
        )

    if result.returncode != 0:
        return render_template(
            "index.html",
            error="Download failed.",
            log=result.stderr or result.stdout,
        )

    return render_template(
        "index.html",
        success=f"Download complete. Saved under {target_dir}.",
        log=result.stdout,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
