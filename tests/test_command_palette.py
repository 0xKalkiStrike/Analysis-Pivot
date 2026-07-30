"""Test Command dataclass + fuzzy scoring behaviour (headless)."""
from __future__ import annotations

from rapidfuzz import fuzz

from bi_platform.ui.dialogs.command_palette import Command


def test_command_searchable_string():
    c = Command(label="Merge Wizard", action=lambda: None, category="Action", hint="Join two datasets")
    assert "merge" in c.searchable
    assert "action" in c.searchable
    assert "join" in c.searchable


def test_command_action_is_called():
    fired = []
    c = Command(label="Fire", action=lambda: fired.append(1))
    c.action()
    assert fired == [1]


def test_command_fuzzy_scoring_ranks_expected_first():
    cmds = [
        Command(label="Open Files", action=lambda: None, category="Action"),
        Command(label="Save Project", action=lambda: None, category="Action"),
        Command(label="Merge Wizard", action=lambda: None, category="Action"),
        Command(label="Go to Dashboard", action=lambda: None, category="Navigate"),
    ]
    q = "merge"
    scored = sorted(cmds, key=lambda c: fuzz.WRatio(q, c.searchable), reverse=True)
    assert scored[0].label == "Merge Wizard"


def test_command_fuzzy_handles_typo():
    cmds = [
        Command(label="Discover Relationships", action=lambda: None, category="Action"),
        Command(label="Open Folder", action=lambda: None, category="Action"),
    ]
    q = "reltionships"  # missing 'a'
    scored = sorted(cmds, key=lambda c: fuzz.WRatio(q, c.searchable), reverse=True)
    assert scored[0].label == "Discover Relationships"
