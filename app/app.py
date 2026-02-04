from __future__ import annotations

import os
import re
import subprocess
from pathlib import Path

from flask import Flask, render_template, request

app = Flask(__name__)

DOWNLOAD_ROOT = Path("/download")
SAFE_SUBDIR_RE = re.compile(r"^[a-zA-Z0-9._-]+(?:/[a-zA-Z0-9._-]+)*$")
MAX_DIR_DEPTH = 6


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


def list_children(root: Path, subdir: str) -> list[str]:
    try:
        target = resolve_target_dir(subdir)
    except ValueError:
        return []
    if not target.exists():
        return []
    if target == root.resolve():
        depth = 0
    else:
        depth = len(target.relative_to(root.resolve()).parts)
    if depth >= MAX_DIR_DEPTH:
        return []
    return sorted([p.name for p in target.iterdir() if p.is_dir() and not p.name.startswith(".")])


@app.get("/")
def index():
    browse_path = (request.args.get("path") or "").strip().strip("/")
    try:
        resolve_target_dir(browse_path)
    except ValueError:
        browse_path = ""
    return render_template(
        "index.html",
        browse_path=browse_path,
        dirs=list_children(DOWNLOAD_ROOT, browse_path),
        url="",
        subdir="",
    )


@app.post("/download")
def download():
    url = (request.form.get("url") or "").strip()
    subdir = (request.form.get("subdir") or "").strip()
    browse_path = (request.form.get("browse_path") or "").strip().strip("/")
    if not url:
        return render_template(
            "index.html",
            error="URL is required.",
            browse_path=browse_path,
            dirs=list_children(DOWNLOAD_ROOT, browse_path),
            url=url,
            subdir=subdir,
        )

    try:
        target_dir = resolve_target_dir(subdir)
    except ValueError as exc:
        return render_template(
            "index.html",
            error=str(exc),
            browse_path=browse_path,
            dirs=list_children(DOWNLOAD_ROOT, browse_path),
            url=url,
            subdir=subdir,
        )

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
            browse_path=browse_path,
            dirs=list_children(DOWNLOAD_ROOT, browse_path),
            url=url,
            subdir=subdir,
        )

    return render_template(
        "index.html",
        success=f"Download complete. Saved under {target_dir}.",
        log=result.stdout,
        browse_path=browse_path,
        dirs=list_children(DOWNLOAD_ROOT, browse_path),
        url=url,
        subdir=subdir,
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8000"))
    app.run(host="0.0.0.0", port=port)
