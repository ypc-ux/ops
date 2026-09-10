"""Entrypoint: python -m digest.digest --mode pulse|wrap [--since ISO8601]
[--dry-run] [--to EMAIL]

Auto-discovers every module in digest/collectors/, calling its collect(since)
function. A collector that raises becomes a `broken` signal about itself so
one bad key or dead API never kills the whole email.
"""
import argparse
import hashlib
import importlib
import json
import pkgutil
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from digest import collectors, mailer, render
from digest.schema import Signal

SENT_LEDGER = Path(__file__).resolve().parent.parent / "state" / "_sent.json"
DEDUPE_WINDOW = timedelta(hours=24)


def discover_signals(since: datetime) -> list[Signal]:
    signals: list[Signal] = []
    for _, name, _ in pkgutil.iter_modules(collectors.__path__):
        module_name = f"digest.collectors.{name}"
        try:
            module = importlib.import_module(module_name)
            signals.extend(module.collect(since))
        except Exception as exc:  # noqa: BLE001
            signals.append(
                Signal(
                    project="ops",
                    kind="broken",
                    title=f"collector {name} failed",
                    detail=str(exc),
                )
            )
    return signals


def _sig_hash(s: Signal) -> str:
    return hashlib.sha1(f"{s.project}:{s.title}".encode()).hexdigest()


def load_ledger() -> dict:
    if SENT_LEDGER.exists():
        try:
            return json.loads(SENT_LEDGER.read_text())
        except Exception:
            return {}
    return {}


def save_ledger(ledger: dict, dry_run: bool) -> None:
    if dry_run:
        return
    SENT_LEDGER.parent.mkdir(parents=True, exist_ok=True)
    SENT_LEDGER.write_text(json.dumps(ledger, indent=2) + "\n")


def dedupe_pulse(signals: list[Signal], ledger: dict, now: datetime) -> list[Signal]:
    urgent = [s for s in signals if s.kind in ("needs_you", "broken")]
    fresh = []
    for s in urgent:
        h = _sig_hash(s)
        last_sent = ledger.get(h)
        if last_sent:
            try:
                if now - datetime.fromisoformat(last_sent) < DEDUPE_WINDOW:
                    continue
            except Exception:
                pass
        fresh.append(s)
        ledger[h] = now.isoformat()
    return fresh


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", choices=["pulse", "wrap"], required=True)
    parser.add_argument("--since", default=None, help="ISO8601 UTC timestamp")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--to", default=None, help="override NOTIFY_TO recipient")
    args = parser.parse_args()

    now = datetime.now(timezone.utc)
    if args.since:
        since = datetime.fromisoformat(args.since)
    else:
        since = now - (timedelta(hours=6) if args.mode == "pulse" else timedelta(hours=24))

    signals = discover_signals(since)

    if args.mode == "pulse":
        ledger = load_ledger()
        signals = dedupe_pulse(signals, ledger, now)
        if not signals:
            print("[ops.digest] pulse: nothing new, suppressing send")
            return 0
        save_ledger(ledger, args.dry_run)

    subject = render.subject(args.mode, signals)
    body = render.render(args.mode, signals, since)

    print(f"Subject: {subject}\n")
    print(body)

    if args.dry_run:
        print("[ops.digest] --dry-run set, not sending")
        return 0

    mailer.send(subject, body, to=args.to)
    print("[ops.digest] sent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
