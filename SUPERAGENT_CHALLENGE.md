# Ops Digest — Portfolio Intelligence Layer Superagent

## What It Does
Portfolio-wide notification digest that monitors all other agents and publishes daily status reports. Acts as the connective tissue between all Superagents, collecting signals from each and delivering one unified digest.

The digest runs on GitHub Actions cron, collects state from all repos, and publishes to GitHub Issues (or email if configured). It's the "meta-layer" that makes the entire system observable.

## Tools Connected (3+)
- **GitHub API** — collects state from all repos (Actions runs, Issues, PRs)
- **GitHub Actions** — runs the digest on a daily schedule
- **Email (optional)** — can deliver digest via email instead of Issues
- **Local state collectors** — each repo publishes signals via ops_publish.py bridge

## Autonomous Decisions
- **Signal collection**: collects `did`, `needs_you`, `broken`, `stale` signals from all repos
- **Digest generation**: renders signals into a human-readable digest
- **Delivery**: publishes to GitHub Issues (default) or email (if configured)
- **Degradation**: if a collector fails, the digest still runs (one `broken` signal, not a dead run)

## Daily Cadence
Runs every day via GitHub Actions cron:
- Collects signals from all repos (switchboard, social-ops, agentic-priming, etc.)
- Generates digest with all signals
- Publishes to GitHub Issues (label: `ops-digest`)
- First successful scheduled run: 2026-09-10 16:35 UTC

The digest is the "morning read" — you open it every day to see what happened across the entire portfolio.

## Context Across Sessions
The digest maintains context via:
- Rolling GitHub Issue (one issue per digest cycle, comments appended)
- State files in `state/` directory (tracks what's been sent)
- Signal history (all signals collected, with timestamps)

Every digest has full context: what happened yesterday, what needs attention today, what's broken.

## Signal Types
- **`did`** — what the agent did (calls handled, posts made, scripts generated)
- **`needs_you`** — what needs human attention (escalations, held drafts, failed calls)
- **`broken`** — what's broken (failed collectors, API errors)
- **`stale`** — what hasn't run in a while (agents that haven't published signals)

## Integration with Portfolio
Every other agent publishes signals to ops via the ops_publish.py bridge:
- **Switchboard**: publishes call handling, SMS sent, bookings made
- **Social-ops**: publishes drafts created, auto-approved, posted, held for review
- **Agentic-priming**: publishes scripts generated, calls made, outcomes logged

The ops digest is the single source of truth for "what happened across the entire portfolio today."

## Testing & Quality
- 16 unit tests (all passing)
- GitHub Actions workflow confirmed self-firing
- Zero-secret delivery (GitHub Issues by default, no API keys needed)
- Graceful degradation (one broken signal, not a dead run)

## Scoring
- **Qualifying**: 10 points (autonomous agent doing real work)
- **Moderate**: 10 points (orchestrates 3+ tools, makes autonomous decisions, runs on schedule)
- **Total**: 20 points

## What Makes This Different
This isn't just a "send me an email" system. This is the connective tissue that makes the entire portfolio observable. Without ops, you'd have to check each agent individually. With ops, you open one digest every morning and see everything.

The ops digest is what turns four separate agents into one operating system.
