"""Failed GitHub Actions workflow runs across your repos -> `broken` signals.
Uses the built-in GITHUB_TOKEN (no new secret needed); when running locally
without a token, this collector no-ops rather than failing the whole digest.
"""
import json
import os
import urllib.request
from datetime import datetime

REPOS = [
    "ypc-ux/ypc-ux",
    "ypc-ux/ops",
]

from ..schema import Signal


def _get(url: str, token: str) -> dict:
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
        },
    )
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())


def collect(since: datetime) -> list[Signal]:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        return []

    out: list[Signal] = []
    since_iso = since.strftime("%Y-%m-%dT%H:%M:%SZ")

    for repo in REPOS:
        url = (
            f"https://api.github.com/repos/{repo}/actions/runs"
            f"?status=failure&created=%3E{since_iso}&per_page=10"
        )
        try:
            data = _get(url, token)
        except Exception as exc:  # noqa: BLE001
            out.append(
                Signal(
                    project=repo,
                    kind="broken",
                    title="could not check GitHub Actions status",
                    detail=str(exc),
                )
            )
            continue

        for run in data.get("workflow_runs", []):
            out.append(
                Signal(
                    project=repo,
                    kind="broken",
                    title=f"workflow failed: {run.get('name')}",
                    detail=f"run #{run.get('run_number')} on {run.get('head_branch')}",
                    ts=run.get("created_at", ""),
                    url=run.get("html_url", ""),
                )
            )

    return out
