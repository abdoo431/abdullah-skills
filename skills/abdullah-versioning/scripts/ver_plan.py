"""Propose the next version, and the entries that decide it, from the [Unreleased] entries."""
from dataclasses import dataclass, field
from typing import Optional

from ver_changelog import NO_ENTRIES, ORDER
from ver_semver import Version, bump, next_pre

_FEATURE = ("Added", "Changed", "Deprecated", "Removed")


@dataclass
class Proposal:
    current: Optional[Version]
    next: Version
    part: str
    reasons: list = field(default_factory=list)
    judgment: list = field(default_factory=list)
    pre: Optional[str] = None


MAX_REASON = 120


def _first_line(bullet: str) -> str:
    """The entry's first sentence, cut to MAX_REASON characters, so a proposal reads in one line."""
    line = bullet.split("\n", 1)[0].strip()
    line = line[2:].strip() if line[:2] in ("- ", "* ", "+ ") else line
    end = line.find(". ")
    if 0 < end < MAX_REASON:
        return line[:end + 1]
    return line if len(line) <= MAX_REASON else line[:MAX_REASON - 1].rstrip() + "…"


def propose(current: Optional[Version], entries: dict, *, first: Version, pre: Optional[str] = None,
            major: bool = False, existing=()) -> Proposal:
    present = {name: items for name, items in entries.items() if items}
    if not present:
        raise ValueError(NO_ENTRIES)
    reasons = [f"{name}: {_first_line(b)}" for name in ORDER if name in present for b in present[name]]
    unknown = [name for name in present if name not in ORDER]
    reasons += [f"{name}: {_first_line(b)}" for name in unknown for b in present[name]]
    judgment = [f"Changed: {_first_line(b)}" for b in present.get("Changed", [])]
    judgment += [f"{name}: {_first_line(b)}" for name in unknown for b in present[name]]

    if current is None:
        part, final = "first", first
    else:
        feature = any(name in present for name in _FEATURE) or bool(unknown)
        if current.major == 0:
            part = "minor" if feature or major else "patch"
        elif major or "Removed" in present:
            part = "major"
        else:
            part = "minor" if feature else "patch"
        final = bump(current.final, part)
    nxt = next_pre(final, pre, list(existing)) if pre else final
    return Proposal(current, nxt, part, reasons, judgment, pre)
