"""Read and edit a Keep a Changelog file for releases.

Functions take and return the whole file text with "\\n" line endings; read_text and
write_text keep the file's own line endings and BOM.
"""
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

from ver_semver import Version

ORDER = ("Added", "Changed", "Deprecated", "Removed", "Fixed", "Security")
NO_ENTRIES = "[Unreleased] has no entries to release"

_UNRELEASED_RE = re.compile(r"^##[ \t]+(\[)?unreleased\]?[ \t]*$", re.I)
_VERSION_RE = re.compile(
    r"^##[ \t]+(\[)?(?P<v>\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)\]?[ \t]*(?:[-–—][ \t]*(?P<d>\S.*?))?[ \t]*$"
)
_H2_RE = re.compile(r"^##[ \t]")
_H3_RE = re.compile(r"^###[ \t]+(.+?)[ \t]*$")
_BULLET_RE = re.compile(r"^[-*+][ \t]")
_LINK_RE = re.compile(r"^\[[^\]]+\]:[ \t]*\S")
_UNRELEASED_LINK_RE = re.compile(r"^\[unreleased\]:[ \t]*(?P<base>\S+?)/compare/(?P<tag>\S+?)\.\.\.HEAD[ \t]*$", re.I)


@dataclass
class Section:
    title: str
    version: Optional[Version]
    date: Optional[str]
    line: int
    entries: dict = field(default_factory=dict)
    start: int = 0  # index of the heading line
    end: int = 0  # index after the section's last line
    bracketed: bool = True


def read_text(path: Path):
    raw = Path(path).read_bytes()
    bom = raw.startswith(b"\xef\xbb\xbf")
    text = raw[3:].decode("utf-8", errors="replace") if bom else raw.decode("utf-8", errors="replace")
    newline = "\r\n" if "\r\n" in text else "\n"
    return text.replace("\r\n", "\n"), newline, bom


def write_text(path: Path, text: str, newline: str, bom: bool) -> None:
    data = text.replace("\n", newline).encode("utf-8")
    Path(path).write_bytes((b"\xef\xbb\xbf" if bom else b"") + data)


def _lines(text: str) -> list:
    return text.split("\n")


def _entries(body: list) -> dict:
    entries, current, bullet = {}, None, None
    for line in body:
        h3 = _H3_RE.match(line)
        if h3:
            current, bullet = h3.group(1), None
            continue
        if _BULLET_RE.match(line):
            entries.setdefault(current or "", []).append(line)
            bullet = len(entries[current or ""]) - 1
        elif bullet is not None and line.strip() and line[:1] in (" ", "\t"):
            items = entries[current or ""]
            items[bullet] += "\n" + line
        elif not line.strip():
            continue
        else:
            bullet = None
    return entries


def sections(text: str) -> list:
    lines = _lines(text)
    found = []
    for i, line in enumerate(lines):
        if _UNRELEASED_RE.match(line):
            found.append(Section("Unreleased", None, None, i + 1, start=i,
                                 bracketed=bool(_UNRELEASED_RE.match(line).group(1))))
            continue
        m = _VERSION_RE.match(line)
        if m:
            try:
                version = Version.parse(m.group("v"))
            except ValueError:
                continue
            found.append(Section(m.group("v"), version, m.group("d"), i + 1, start=i, bracketed=bool(m.group(1))))
    for sec in found:
        j = sec.start + 1
        while j < len(lines) and not _H2_RE.match(lines[j]) and not _LINK_RE.match(lines[j]):
            j += 1
        sec.end = j
        sec.entries = _entries(lines[sec.start + 1:j])
    return found


def _unreleased_section(secs: list) -> Optional[Section]:
    return next((s for s in secs if s.title == "Unreleased"), None)


def _find(secs: list, version: Version) -> Section:
    for s in secs:
        if s.version == version:
            return s
    raise ValueError(f"no [{version}] section in the changelog")


def unreleased(text: str) -> dict:
    sec = _unreleased_section(sections(text))
    return sec.entries if sec else {}


def _trim(block: list) -> list:
    while block and not block[0].strip():
        block = block[1:]
    while block and not block[-1].strip():
        block = block[:-1]
    return block


def _heading(version: Version, date: Optional[str], bracketed: bool) -> str:
    label = f"[{version}]" if bracketed else str(version)
    return f"## {label} - {date}" if date else f"## {label}"


def _join(parts: list) -> str:
    return "\n".join(parts)


def cut(text: str, version: Version, date: str, previous_tag: Optional[str], tag_format: str) -> str:
    lines = _lines(text)
    secs = sections(text)
    un = _unreleased_section(secs)
    if un is None or not any(un.entries.values()):
        raise ValueError(NO_ENTRIES)
    body = _trim(lines[un.start + 1:un.end])
    new = lines[:un.start + 1] + ["", _heading(version, date, un.bracketed), ""] + body + [""] + lines[un.end:]
    out = _join(new)
    return _update_links(out, version, previous_tag, tag_format)


def _update_links(text: str, version: Version, previous_tag: Optional[str], tag_format: str) -> str:
    lines = _lines(text)
    new_tag = tag_format.replace("{version}", str(version))
    for i, line in enumerate(lines):
        m = _UNRELEASED_LINK_RE.match(line)
        if not m:
            continue
        base = m.group("base")
        label = line[:line.index("]") + 1]
        lines[i] = f"{label}: {base}/compare/{new_tag}...HEAD"
        target = f"{base}/compare/{previous_tag}...{new_tag}" if previous_tag else f"{base}/releases/tag/{new_tag}"
        lines.insert(i + 1, f"[{version}]: {target}")
        break
    return _join(lines)


def replace_section(text: str, heading_and_body: str, version: Version) -> str:
    """Replace this text's [version] section with another branch's copy of it (a back-merge).

    Entries only this branch's copy has are this branch's own work, misplaced by the merge:
    they move back under [Unreleased], in their subsections.
    """
    secs = sections(text)
    target = _find(secs, version)
    block = _trim(_lines(heading_and_body.replace("\r\n", "\n")))
    theirs = _entries(block[1:])
    moved = {name: [b for b in items if b not in theirs.get(name, [])] for name, items in target.entries.items()}
    moved = {name: items for name, items in moved.items() if items}
    lines = _lines(text)
    out = lines[:target.start] + block + [""] + lines[target.end:]
    if not moved:
        return _join(out)
    text = _join(out)
    un = _unreleased_section(sections(text))
    if un is None:
        raise ValueError("no [Unreleased] section to move this branch's own entries to")
    lines = _lines(text)
    pre, blocks = _blocks(lines[un.start + 1:un.end])
    for name, items in moved.items():
        body = [line for item in items for line in item.split("\n")]
        same = next((b for b in blocks if b[0] == name), None)
        if same:
            same[1] = _trim(same[1]) + body
            continue
        at = next((i for i, b in enumerate(blocks) if _rank(b[0]) > _rank(name)), len(blocks))
        blocks.insert(at, [name, body])
    rendered = [lines[un.start], ""] + (_trim(pre) + [""] if _trim(pre) else [])
    for name, body in blocks:
        rendered += [f"### {name}", ""] + _trim(body) + [""]
    return _join(lines[:un.start] + rendered + lines[un.end:])


def _blocks(body: list):
    """(lines before the first ### heading, [[name, lines under the heading], ...]), every line kept."""
    pre, blocks = [], []
    for line in body:
        h3 = _H3_RE.match(line)
        if h3:
            blocks.append([h3.group(1), []])
        elif blocks:
            blocks[-1][1].append(line)
        else:
            pre.append(line)
    return pre, blocks


def _rank(name: str) -> int:
    return ORDER.index(name) if name in ORDER else len(ORDER)


def fold_unreleased_into(text: str, version: Version) -> str:
    """Move the [Unreleased] entries into the open [version] section, keeping every line of both."""
    secs = sections(text)
    un = _unreleased_section(secs)
    if un is None or not any(un.entries.values()):
        return text
    target = _find(secs, version)
    lines = _lines(text)
    un_pre, un_blocks = _blocks(lines[un.start + 1:un.end])
    pre, blocks = _blocks(lines[target.start + 1:target.end])
    pre = _trim(pre)
    if _trim(un_pre):
        pre = pre + ([""] if pre else []) + _trim(un_pre)
    for name, body in un_blocks:
        body = _trim(body)
        if not body:
            continue
        same = next((b for b in blocks if b[0] == name), None)
        if same:
            same[1] = _trim(same[1]) + body
            continue
        at = next((i for i, b in enumerate(blocks) if _rank(b[0]) > _rank(name)), len(blocks))
        blocks.insert(at, [name, body])
    rendered = [lines[target.start], ""] + (pre + [""] if pre else [])
    for name, body in blocks:
        rendered += [f"### {name}", ""] + _trim(body) + [""]
    replacement = {
        un.start: [lines[un.start], ""],
        target.start: rendered,
    }
    out, cursor = [], 0
    for sec in sorted([un, target], key=lambda s: s.start):
        out += lines[cursor:sec.start] + replacement[sec.start]
        cursor = sec.end
    out += lines[cursor:]
    return _join(out)


def set_date(text: str, version: Version, date: str) -> str:
    sec = _find(sections(text), version)
    lines = _lines(text)
    lines[sec.start] = _heading(version, date, sec.bracketed)
    return _join(lines)


def section_body(text: str, version: Version) -> str:
    sec = _find(sections(text), version)
    return _join(_trim(_lines(text)[sec.start + 1:sec.end]))


def insert_section(text: str, heading_and_body: str, version: Version) -> str:
    secs = sections(text)
    if any(s.version == version for s in secs):
        raise ValueError(f"[{version}] is already in the changelog")
    lines = _lines(text)
    block = _trim(_lines(heading_and_body.replace("\r\n", "\n")))
    below = next((s for s in secs if s.version is not None and s.version < version), None)
    if below is not None:
        at = below.start
        return _join(lines[:at] + block + [""] + lines[at:])
    at = secs[-1].end if secs else len(lines)
    head = lines[:at]
    while head and not head[-1].strip():
        head.pop()
    return _join(head + [""] + block + [""] + lines[at:])


def problems(text: str) -> list:
    secs = sections(text)
    found = []
    if _unreleased_section(secs) is None:
        found.append((1, "no [Unreleased] section"))
    seen = {}
    previous = None
    for sec in secs:
        if sec.version is None:
            continue
        if sec.version in seen:
            found.append((sec.line, f"[{sec.version}] appears twice (first on line {seen[sec.version]})"))
        else:
            seen[sec.version] = sec.line
            if previous is not None and sec.version > previous.version:
                found.append((sec.line, f"[{sec.version}] is below [{previous.version}]: sections are out of order"))
        previous = sec
    return found


def fold_candidates(text: str, version: Version) -> list:
    sec = _find(sections(text), version)
    if "Added" not in sec.entries:
        return []
    return list(sec.entries.get("Fixed", []))
