"""ADR file names, numbering, index rows and templates."""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Optional

ADR_NAME_RE = re.compile(r"^(\d{3,4})-[a-z0-9][a-z0-9-]*\.md$")
_LOOKS_LIKE_ADR_RE = re.compile(r"^(?:adr[-_])?\d+[-_ ]", re.I)
_LINK_RE = re.compile(r"\[[^\]]*\]\(\s*<?([^)>\s]+)")
_SEPARATOR_RE = re.compile(r"^\s*\|?\s*:?-{3,}:?\s*(\|\s*:?-{3,}:?\s*)*\|?\s*$")
_LIST_RE = re.compile(r"^\s*(?:[-*+]|\d+[.)])\s+")
_STATUS_WORD_RE = re.compile(
    r"^(proposed|accepted|rejected|deprecated|superseded|draft|approved|withdrawn|amended)"
    r"(\s+(by|in|with|on|from|until|as)\b.*)?$",
    re.I,
)
_SLUG_MAX = 60


class IndexFormatError(ValueError):
    """The ADR index is neither a table nor a list of links."""


@dataclass(frozen=True)
class AdrFile:
    number: int
    name: str


def adr_files(names: Iterable[str]) -> list[AdrFile]:
    found = []
    for name in names:
        m = ADR_NAME_RE.match(name)
        if m and int(m.group(1)) > 0:
            found.append(AdrFile(int(m.group(1)), name))
    return sorted(found, key=lambda f: (f.number, f.name))


def number_width(files: list[AdrFile]) -> int:
    if not files:
        return 4
    latest = max(files, key=lambda f: f.number)
    return len(latest.name.split("-", 1)[0])


def next_number(local: list[AdrFile], base: list[AdrFile]) -> int:
    return max([f.number for f in local] + [f.number for f in base] + [0]) + 1


def slugify(title: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    if len(slug) > _SLUG_MAX:
        cut = slug[:_SLUG_MAX]
        slug = cut[: cut.rfind("-")] if slug[_SLUG_MAX] != "-" and "-" in cut else cut
        slug = slug.strip("-")
    return slug


def unrecognised_adrs(names: Iterable[str]) -> list[str]:
    return [
        n for n in names
        if n.lower().endswith(".md") and _LOOKS_LIKE_ADR_RE.match(n) and not ADR_NAME_RE.match(n)
    ]


def project_template(adr_dir: Path) -> Optional[Path]:
    for name in ("0000-template.md", "template.md"):
        if (Path(adr_dir) / name).is_file():
            return Path(adr_dir) / name
    return None


# ---------------------------------------------------------------- index

def _adr_link_name(line: str) -> Optional[str]:
    for m in _LINK_RE.finditer(line):
        name = m.group(1).split("#", 1)[0].rsplit("/", 1)[-1]
        if ADR_NAME_RE.match(name):
            return name
    return None


def index_targets(text: str) -> list[tuple[int, str]]:
    found = []
    for i, line in enumerate(text.split("\n"), 1):
        for m in _LINK_RE.finditer(line):
            name = m.group(1).split("#", 1)[0].rsplit("/", 1)[-1]
            if ADR_NAME_RE.match(name):
                found.append((i, name))
    return found


def _cells(line: str) -> list[str]:
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|") and not s.endswith("\\|"):
        s = s[:-1]
    return [c.strip() for c in re.split(r"(?<!\\)\|", s)]


def _is_row(line: str) -> bool:
    return line.strip().startswith("|")


def _link_lines(lines: list[str]) -> list[int]:
    return [i for i, line in enumerate(lines) if _adr_link_name(line) and (_is_row(line) or _LIST_RE.match(line))]


def _header_table_end(lines: list[str]) -> Optional[int]:
    """Index of the separator line of the last header+separator table, or None."""
    end = None
    for i in range(1, len(lines)):
        if "|" in lines[i] and _SEPARATOR_RE.match(lines[i]) and "|" in lines[i - 1]:
            end = i
    return end


def _table_header(lines: list[str], row: int) -> Optional[list[str]]:
    """Header cells of the table holding the given row, or None when it has no header."""
    k = row
    while k > 0 and _is_row(lines[k]):
        if _SEPARATOR_RE.match(lines[k]) and _is_row(lines[k - 1]):
            return _cells(lines[k - 1])
        k -= 1
    return None


def index_format(text: str) -> Optional[str]:
    lines = text.split("\n")
    links = _link_lines(lines)
    if links:
        return "table" if _is_row(lines[links[-1]]) else "list"
    return "table" if _header_table_end(lines) is not None else None


def _insert_after(lines: list[str], i: int, new: str, crlf: bool) -> list[str]:
    if crlf:
        if i == len(lines) - 1:
            lines[i] += "\r"
        else:
            new += "\r"
    return lines[: i + 1] + [new] + lines[i + 1:]


def _table_row(ref_cells: list[str], link_idx: int, status_idx: Optional[int], title_idx: Optional[int],
               number: str, name: str, title: str) -> str:
    cells = [""] * len(ref_cells)
    cells[link_idx] = f"[{number}]({name})"
    if title_idx is not None:
        cells[title_idx] = title.replace("|", "\\|")
    if status_idx is not None:
        cells[status_idx] = "Proposed"
    return "| " + " | ".join(cells) + " |"


def insert_index_row(text: str, number: str, name: str, title: str) -> str:
    lines = text.split("\n")
    crlf = "\r\n" in text
    links = _link_lines(lines)
    if links and _is_row(lines[links[-1]]):
        i = links[-1]
        cells = _cells(lines[i])
        link_idx = next(k for k, c in enumerate(cells) if _adr_link_name(c))
        header = _table_header(lines, i)
        status_idx = None
        if header:
            status_idx = next(
                (k for k, c in enumerate(header) if "status" in c.lower() and k != link_idx and k < len(cells)), None
            )
        else:
            status_idx = next((k for k, c in enumerate(cells) if k != link_idx and _STATUS_WORD_RE.match(c)), None)
        title_idx = next(
            (k for k, c in enumerate(cells) if k not in (link_idx, status_idx) and c), None
        )
        new = _table_row(cells, link_idx, status_idx, title_idx, number, name, title)
        while i + 1 < len(lines) and _is_row(lines[i + 1]):
            i += 1
        return "\n".join(_insert_after(lines, i, new, crlf))
    if links:
        i = links[-1]
        line = lines[i].rstrip("\r")
        m = _LINK_RE.search(line)
        link_end = line.find(")", m.end()) + 1
        sep = re.match(r"^[\s:\u2013\u2014-]*", line[link_end:]).group(0) or " "
        new = f"{line[:m.start()]}[{number}]({name}){sep}{title}"
        return "\n".join(_insert_after(lines, i, new, crlf))
    sep_idx = _header_table_end(lines)
    if sep_idx is None:
        raise IndexFormatError("the index is neither a table nor a list of links")
    header = _cells(lines[sep_idx - 1])
    status_idx = next((k for k, c in enumerate(header) if "status" in c.lower() and k != 0), None)
    title_idx = 1 if len(header) > 1 and status_idx != 1 else None
    new = _table_row(header, 0, status_idx, title_idx, number, name, title)
    i = sep_idx
    while i + 1 < len(lines) and _is_row(lines[i + 1]):
        i += 1
    return "\n".join(_insert_after(lines, i, new, crlf))


# ------------------------------------------------------- status and date

def _field(text: str, key: str) -> Optional[tuple[int, str, int, int]]:
    pattern = re.compile(
        rf"(?:^\s*(?:[-*+]\s+)?|\u00b7\s*)(?:\*\*|__)?{key}(?:\*\*|__)?\s*:\s*(?:\*\*|__)?\s*(.*?)\s*(?:\s\u00b7\s|$)",
        re.I,
    )
    heading = re.compile(rf"^#{{2,}}\s+{key}\s*$", re.I)
    lines = text.split("\n")
    for i, line in enumerate(lines, 1):
        m = pattern.search(line)
        if m:
            return i, m.group(1), m.start(1), m.end(1)
        if heading.match(line.rstrip()):
            for j in range(i, len(lines)):
                value = lines[j].strip()
                if value:
                    start = len(lines[j]) - len(lines[j].lstrip())
                    return j + 1, value, start, start + len(value)
            return None
    return None


def status_of(text: str) -> Optional[tuple[int, str]]:
    f = _field(text, "Status")
    return (f[0], f[1]) if f else None


def date_of(text: str) -> Optional[tuple[int, str]]:
    f = _field(text, "Date")
    return (f[0], f[1]) if f else None


def render(template: str, number: str, title: str, today: str, numbered_h1: bool) -> str:
    text = template.replace("\r\n", "\n")
    lines = text.split("\n")
    heading = f"# {number}. {title}" if numbered_h1 else f"# {title}"
    for i, line in enumerate(lines):
        if line.startswith("# "):
            lines[i] = heading
            break
    text = "\n".join(lines)
    text = text.replace("{number}", number).replace("{title}", title)
    text = text.replace("{date}", today).replace("YYYY-MM-DD", today)
    f = _field(text, "Status")
    if f:
        lines = text.split("\n")
        line = lines[f[0] - 1]
        lead = " " if f[2] > 0 and not line[f[2] - 1].isspace() else ""
        lines[f[0] - 1] = line[: f[2]] + lead + "Proposed" + line[f[3]:]
        text = "\n".join(lines)
    return text
