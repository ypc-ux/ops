# ops

Portfolio-wide notification digest. Local projects (`social-ops`,
`agentic_priming_pilot`) publish state here via `digest.publish.publish()`;
cloud sources are read live by collectors. One GitHub Actions job assembles
everything and emails a single digest — see `.github/workflows/digest.yml`.

- Add a project: drop a file in `digest/collectors/` implementing
  `collect(since: datetime) -> list[Signal]` (see `digest/schema.py`).
- Local dev loop: `python -m digest.digest --mode wrap --dry-run`
- No Deerflow. No dashboard. See the parent conversation's plan for the
  full rationale (`ypc-ux` repo, "Make the portfolio report to you").
