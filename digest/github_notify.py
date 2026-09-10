"""Deliver the digest as a GitHub Issue instead of email — zero secrets to
configure. GITHUB_TOKEN is issued automatically to every Actions run; GitHub
already notifies repo owners/watchers on new issues and comments, so this
gets the digest to you with nothing for you to set up.

The daily wrap keeps ONE rolling issue (found by title prefix) and appends a
comment per run, so it reads as a log rather than spawning a new issue every
day. The pulse always opens a fresh issue — it only fires when something
needs attention, so each one is its own actionable item.
"""
import json
import os
import urllib.error
import urllib.request

API = "https://api.github.com"
WRAP_TITLE_PREFIX = "[ops] daily wrap"


class NotifyConfigError(RuntimeError):
    pass


def _request(method: str, path: str, token: str, payload: dict | None = None) -> dict:
    url = f"{API}{path}"
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub API {method} {path} -> {exc.code}: {exc.read().decode()[:300]}")


def _find_open_wrap_issue(repo: str, token: str) -> dict | None:
    data = _request(
        "GET",
        f"/repos/{repo}/issues?state=open&labels=ops-digest&per_page=20",
        token,
    )
    for issue in data:
        if issue.get("title", "").startswith(WRAP_TITLE_PREFIX):
            return issue
    return None


def notify(mode: str, subject: str, body: str, repo: str | None = None) -> str:
    """Post the digest to GitHub Issues. Returns the issue URL. Raises
    NotifyConfigError if GITHUB_TOKEN isn't set — the one thing this needs,
    and it's provided automatically inside GitHub Actions."""
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise NotifyConfigError(
            "GITHUB_TOKEN is not set — this only runs unauthenticated locally; "
            "inside GitHub Actions it's provided automatically"
        )
    target_repo = repo or os.environ.get("GITHUB_REPOSITORY", "ypc-ux/ops")

    if mode == "wrap":
        existing = _find_open_wrap_issue(target_repo, token)
        if existing:
            _request(
                "POST",
                f"/repos/{target_repo}/issues/{existing['number']}/comments",
                token,
                {"body": f"## {subject}\n\n```\n{body}\n```"},
            )
            return existing["html_url"]
        issue = _request(
            "POST",
            f"/repos/{target_repo}/issues",
            token,
            {
                "title": subject,
                "body": f"```\n{body}\n```",
                "labels": ["ops-digest"],
            },
        )
        return issue["html_url"]

    # pulse: always a fresh issue, it only fires when something needs you
    issue = _request(
        "POST",
        f"/repos/{target_repo}/issues",
        token,
        {
            "title": subject,
            "body": f"```\n{body}\n```",
            "labels": ["ops-digest", "needs-you"],
        },
    )
    return issue["html_url"]
