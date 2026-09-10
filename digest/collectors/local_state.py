"""Reads state/*.json written by publish.py. Emits each project's signals plus
a `stale` signal if a project hasn't published in >48h — silence reported as
silence, never as health.
"""
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

from ..schema import Signal

STATE_DIR = Path(__file__).resolve().parent.parent.parent / "state"
STALE_AFTER = timedelta(hours=48)


def collect(since: datetime) -> list[Signal]:
    out: list[Signal] = []
    if not STATE_DIR.exists():
        return out

    now = datetime.now(timezone.utc)

    for path in sorted(STATE_DIR.glob("*.json")):
        if path.name == "_sent.json":
            continue
        try:
            payload = json.loads(path.read_text())
        except Exception as exc:  # noqa: BLE001
            out.append(
                Signal(
                    project=path.stem,
                    kind="broken",
                    title=f"state file {path.name} is unreadable",
                    detail=str(exc),
                )
            )
            continue

        project = payload.get("project", path.stem)
        generated_at_raw = payload.get("generated_at")
        try:
            generated_at = datetime.fromisoformat(generated_at_raw)
        except Exception:
            generated_at = None

        if generated_at is not None and now - generated_at > STALE_AFTER:
            out.append(
                Signal(
                    project=project,
                    kind="stale",
                    title=f"no local update in {(now - generated_at).days}d",
                    detail=f"last published {generated_at_raw}",
                )
            )

        for raw in payload.get("signals", []):
            sig = Signal.from_dict(raw)
            if sig.ts:
                try:
                    ts = datetime.fromisoformat(sig.ts)
                    if ts < since:
                        continue
                except Exception:
                    pass
            out.append(sig)

    return out
