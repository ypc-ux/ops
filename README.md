# ops

Portfolio-wide notification digest. See `CLAUDE.md` for the shape of the
system. This is the setup checklist to make it actually send mail.

## One-time setup

1. **Add repo secrets** (Settings → Secrets and variables → Actions):
   - `GMAIL_USER` — the sending Gmail address
   - `GMAIL_APP_PASSWORD` — a Gmail [app password](https://myaccount.google.com/apppasswords), not your normal password
   - `NOTIFY_TO` — where the digest goes
2. Nothing else. `GITHUB_TOKEN` for the `gha` collector is provided
   automatically by Actions.

## Verifying it works

```bash
# 1. Render locally, no send, no state touched
python -m digest.digest --mode wrap --dry-run

# 2. Replay canned fixtures instead of waiting for real state/crons
python -m digest.digest --mode wrap --fixtures digest/fixtures --since 2026-09-01T00:00:00Z

# 3. Run the test suite
python -m unittest discover -s tests -v

# 4. First real send, to a filterable/deletable plus-address
python -m digest.digest --mode wrap --to youraddress+opstest@example.com
```

Cloud path, once secrets are set: run the `ops digest` workflow manually
(`workflow_dispatch`) with `dry_run: true` first — proves checkout + secrets
+ Python in ~40s without sending anything — then run it once with
`dry_run: false`.

## Adding a project

Two ways in:

- **Local project** (no cloud API): call `digest.publish.publish(project, signals)`
  from that project's CLI/pipeline. It writes `state/<project>.json` and
  commits+pushes it here. See `ypc-ux/agentic_priming_pilot/phase3/ops_publish.py`
  for the reference bridge — it locates a sibling `ops` checkout (or
  `OPS_REPO_PATH`) and no-ops safely if it's missing, so a project never
  breaks just because `ops` isn't checked out on that machine.
- **Cloud project**: add one file to `digest/collectors/` implementing
  `collect(since: datetime) -> list[Signal]`. It's auto-discovered — nothing
  else to wire. A collector that raises becomes a `broken` signal about
  itself rather than killing the whole run.

## Cadence

- **Pulse** (~4x/day): sends only when there's something `needs_you` or
  `broken`, deduped 24h by `sha1(project+title)` so one stuck item doesn't
  nag repeatedly.
- **Daily wrap**: always sends, even empty — it's the heartbeat proving the
  pipe is alive.
