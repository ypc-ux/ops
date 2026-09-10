"""Shared signal type every collector and the renderer speak."""
from dataclasses import dataclass, asdict, field
from datetime import datetime, timezone

KINDS = ("needs_you", "broken", "stale", "did")


@dataclass
class Signal:
    project: str
    kind: str  # needs_you | broken | stale | did
    title: str
    detail: str = ""
    ts: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    url: str = ""

    def __post_init__(self):
        if self.kind not in KINDS:
            raise ValueError(f"unknown signal kind {self.kind!r}, must be one of {KINDS}")

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> "Signal":
        return cls(
            project=d["project"],
            kind=d["kind"],
            title=d["title"],
            detail=d.get("detail", ""),
            ts=d.get("ts", ""),
            url=d.get("url", ""),
        )
