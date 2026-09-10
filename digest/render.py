"""Plaintext rendering — grouped by kind then project. Phone-readable, no deps."""
from .schema import Signal

KIND_LABEL = {
    "needs_you": "NEEDS YOU",
    "broken": "BROKEN",
    "stale": "STALE",
    "did": "DID",
}
KIND_ORDER = ("needs_you", "broken", "stale", "did")


def subject(mode: str, signals: list[Signal]) -> str:
    by_kind = {k: [s for s in signals if s.kind == k] for k in KIND_ORDER}

    if mode == "pulse":
        urgent = by_kind["needs_you"] + by_kind["broken"]
        projects = sorted({s.project for s in urgent})
        return f"[ops] {len(urgent)} need you — {', '.join(projects)}"

    did_count = len(by_kind["did"])
    open_count = len(by_kind["needs_you"]) + len(by_kind["broken"])
    return f"[ops] daily wrap — {did_count} shipped, {open_count} open"


def render(mode: str, signals: list[Signal], since) -> str:
    lines = [f"ops digest ({mode}) — since {since.isoformat()}", ""]

    if not signals:
        lines.append("Nothing to report.")
        return "\n".join(lines)

    for kind in KIND_ORDER:
        group = [s for s in signals if s.kind == kind]
        if not group:
            continue
        lines.append(f"== {KIND_LABEL[kind]} ==")
        by_project: dict[str, list[Signal]] = {}
        for s in group:
            by_project.setdefault(s.project, []).append(s)
        for project in sorted(by_project):
            lines.append(f"  {project}:")
            for s in by_project[project]:
                line = f"    - {s.title}"
                if s.url:
                    line += f" ({s.url})"
                lines.append(line)
                if s.detail:
                    lines.append(f"      {s.detail}")
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"
