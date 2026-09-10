"""Stdlib unittest — no pytest dependency, matching the rest of the repo."""
import sys
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from digest import digest, render
from digest.schema import Signal


def sig(project="proj", kind="did", title="something happened", ts=None):
    return Signal(project=project, kind=kind, title=title, ts=ts or now_iso())


def now_iso():
    return datetime.now(timezone.utc).isoformat()


class TestSchema(unittest.TestCase):
    def test_rejects_unknown_kind(self):
        with self.assertRaises(ValueError):
            Signal(project="p", kind="nonsense", title="x")

    def test_round_trips_through_dict(self):
        s = sig(kind="broken", title="db down")
        self.assertEqual(Signal.from_dict(s.to_dict()), s)


class TestRender(unittest.TestCase):
    def test_empty_signals_says_nothing_to_report(self):
        body = render.render("wrap", [], datetime.now(timezone.utc))
        self.assertIn("Nothing to report", body)

    def test_groups_by_kind_then_project(self):
        signals = [
            sig(project="b-proj", kind="did", title="shipped b"),
            sig(project="a-proj", kind="did", title="shipped a"),
            sig(project="a-proj", kind="needs_you", title="stuck a"),
        ]
        body = render.render("wrap", signals, datetime.now(timezone.utc))
        needs_idx = body.index("NEEDS YOU")
        did_idx = body.index("DID")
        self.assertLess(needs_idx, did_idx)  # needs_you group comes before did
        # within DID, projects appear in sorted order
        self.assertLess(body.index("a-proj", did_idx), body.index("b-proj", did_idx))

    def test_pulse_subject_lists_urgent_projects(self):
        signals = [sig(project="switchboard", kind="needs_you"), sig(project="lever-site", kind="broken")]
        subj = render.subject("pulse", signals)
        self.assertIn("2 need you", subj)
        self.assertIn("switchboard", subj)
        self.assertIn("lever-site", subj)

    def test_wrap_subject_counts_shipped_and_open(self):
        signals = [sig(kind="did"), sig(kind="did"), sig(kind="needs_you")]
        subj = render.subject("wrap", signals)
        self.assertIn("2 shipped", subj)
        self.assertIn("1 open", subj)


class TestDedupe(unittest.TestCase):
    def test_first_occurrence_passes_through(self):
        now = datetime.now(timezone.utc)
        signals = [sig(project="p", kind="needs_you", title="stuck")]
        fresh = digest.dedupe_pulse(signals, ledger={}, now=now)
        self.assertEqual(len(fresh), 1)

    def test_repeat_within_window_is_suppressed(self):
        now = datetime.now(timezone.utc)
        s = sig(project="p", kind="needs_you", title="stuck")
        ledger = {digest._sig_hash(s): (now - timedelta(hours=1)).isoformat()}
        fresh = digest.dedupe_pulse([s], ledger, now)
        self.assertEqual(fresh, [])

    def test_repeat_after_window_passes_through_again(self):
        now = datetime.now(timezone.utc)
        s = sig(project="p", kind="needs_you", title="stuck")
        ledger = {digest._sig_hash(s): (now - timedelta(hours=25)).isoformat()}
        fresh = digest.dedupe_pulse([s], ledger, now)
        self.assertEqual(len(fresh), 1)

    def test_did_signals_are_never_deduped_or_urgent(self):
        now = datetime.now(timezone.utc)
        s = sig(project="p", kind="did", title="shipped")
        fresh = digest.dedupe_pulse([s], ledger={}, now=now)
        self.assertEqual(fresh, [])  # `did` isn't urgent, so it's excluded from pulse entirely


if __name__ == "__main__":
    unittest.main()
