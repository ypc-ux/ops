# Handoff — continuing outside Claude Code

State as of 2026-09-10, ~17:15 UTC. Picking this up in VS Code (or any
local clone) needs no special setup — it's a plain Python/stdlib repo with
one GitHub Actions workflow. This file is the map back in.

## What's live right now

- `ypc-ux/ops` @ `main`, commit `34e33b2` — Phase 1 digest pipe. Fully
  working: `.github/workflows/digest.yml` cron confirmed self-firing
  (first successful scheduled run: 2026-09-10 16:35 UTC,
  https://github.com/ypc-ux/ops/actions/runs/34503090616). Delivers to
  GitHub Issues (label `ops-digest`) by default — zero secrets required.
  `.github/workflows/test.yml` runs the unit suite on every push.
- `ypc-ux/ypc-ux` @ branch `claude/portfolio-notification-audit-s87qs8`,
  commit `337ce67` — `agentic_priming_pilot/phase3/` wired to publish
  state into `ops` via `phase3/ops_publish.py`. Also corrected the
  phantom-Deerflow references in `deerflow_workflow.yaml`.

Both trees are clean — nothing uncommitted, nothing unpushed. `git clone`
either and you're at the exact state this session left.

## Clone commands

```bash
git clone https://github.com/ypc-ux/ops
git clone -b claude/portfolio-notification-audit-s87qs8 https://github.com/ypc-ux/ypc-ux
```

## What's NOT done, in priority order

1. **`social-ops` is unwired.** Its `orchestrator.py` only calls
   `notify_slack()` from `_hold()` — pings on failure, never on success,
   no schedule. It needs the same treatment `agentic_priming_pilot` got:
   a `publish()` call (see `phase3/ops_publish.py` as the reference
   pattern — locate a sibling `ops` checkout, no-op safely if absent) at
   the end of a run, publishing both `did` (success) and `needs_you`
   (held) signals. This is the single highest-value remaining piece —
   it's the project with the worst notification gap in the whole audit.

2. **Phase 2 cloud collectors don't exist.** Each is one file in
   `digest/collectors/` implementing `collect(since) -> list[Signal]`
   (see `digest/collectors/gha.py` for the shape) — auto-discovered,
   nothing else to wire:
   - `switchboard.py` — Supabase REST: queued/deferred messages,
     escalations, errors. Needs `SWITCHBOARD_SUPABASE_URL` +
     `SWITCHBOARD_SERVICE_KEY`.
   - `notion.py` — new Ascent form submissions since last digest. Needs
     `NOTION_TOKEN`.
   - `brand_vault.py` — Vercel Postgres: posting streak, missed days.
     Wraps `brand-vault/src/db/queries/sunday-resets.ts:weekStats()`.
     Needs `BRAND_VAULT_POSTGRES_URL`.
   - `lever_site.py` — Supabase: outcome reports, whether the Monday
     `/api/outcomes/adjust` cron actually changed weights. Needs
     `LEVER_SUPABASE_*`.
   Add each secret as a repo secret on `ypc-ux/ops` as you build the
   matching collector — the digest already degrades safely (one
   `broken` signal, not a dead run) if a collector's secret is missing.

3. **Switchboard's cron is still unscheduled.** Create
   `switchboard/vercel.json`:
   ```json
   {"crons":[{"path":"/api/cron/drain","schedule":"*/15 * * * *"}]}
   ```
   The route is already written and auth'd — this file was just never
   created, so quiet-hours-deferred SMS silently never send.
   **`sms_dry_run` stays `true`** until you deliberately flip it after
   A2P 10DLC approval — don't change that as part of this fix.

4. **`jbuilds/.claude/integration-advisor.md` is misfiled.** It's at
   `.claude/` root instead of `.claude/agents/`, with no YAML
   frontmatter, so Claude Code never loads it. Move it, add
   `name`/`description` frontmatter.

5. **Optional: email delivery.** Currently unused — GitHub Issues is the
   working default. Only relevant if you specifically want email over
   issues; see README's "Optional: switch delivery to email" section.

## Verifying you're in a good state before continuing

```bash
cd ops
python -m unittest discover -s tests -v        # 16 tests, should all pass
python -m digest.digest --mode wrap --dry-run   # renders against real state/, doesn't send
```

## Housekeeping

- The hourly Claude Code Routine (`ops progress check-in`,
  `trig_01UXtjZ2B4SNYsgjhxioqnTq`) that was watching this in the
  background is a Claude-Code-only mechanism — it does nothing for you
  in VS Code and should probably be stopped once you're driving from
  there, to avoid duplicate/stale notifications. Ask whoever has access
  to the Claude session to disable it, or just ignore its emails if you
  leave it running — it only fires on real state changes.
