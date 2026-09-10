"""publish() — called by local projects (social-ops, agentic_priming_pilot) to
write their signals to state/<project>.json and commit+push them to this repo.

Wrapped so a broken publish can never break the caller's own run: swallow
everything, print a warning, move on.
"""
import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from .schema import Signal

STATE_DIR = Path(__file__).resolve().parent.parent / "state"


def publish(project: str, signals: list[Signal]) -> bool:
    try:
        STATE_DIR.mkdir(parents=True, exist_ok=True)
        path = STATE_DIR / f"{project}.json"
        payload = {
            "project": project,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "signals": [s.to_dict() for s in signals],
        }
        path.write_text(json.dumps(payload, indent=2) + "\n")

        repo_dir = STATE_DIR.parent
        subprocess.run(["git", "add", str(path)], cwd=repo_dir, check=True)
        diff = subprocess.run(
            ["git", "diff", "--cached", "--quiet"], cwd=repo_dir
        )
        if diff.returncode == 0:
            return True  # nothing changed, nothing to commit

        subprocess.run(
            ["git", "commit", "-m", f"state: {project} {payload['generated_at']}"],
            cwd=repo_dir,
            check=True,
        )
        subprocess.run(["git", "push"], cwd=repo_dir, check=True)
        return True
    except Exception as exc:  # noqa: BLE001 — publish must never crash the caller
        print(f"[ops.publish] failed to publish state for {project}: {exc}")
        return False
