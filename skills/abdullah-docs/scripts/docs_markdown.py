"""Small Markdown helpers: links, backticked paths, heading slugs."""
import re
from dataclasses import dataclass
from typing import Optional
from urllib.parse import unquote

_FENCE_RE = re.compile(r"^ {0,3}(`{3,}|~{3,})")
_INLINE_CODE_RE = re.compile(r"(`+)(.+?)\1")
_INLINE_LINK_RE = re.compile(
    r"\[[^\]]*\]\(\s*(<[^>]*>|[^)\s]*)(?:\s+(?:\"[^\"]*\"|'[^']*'))?\s*\)"
)
_REF_DEF_RE = re.compile(r"^ {0,3}\[(?!\^)[^\]]+\]:\s*(<[^>]*>|\S+)")
_SCHEME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9+.\-]*:")
_HEADING_RE = re.compile(r"^ {0,3}#{1,6}[ \t]+(.*?)[ \t]*(?:#+[ \t]*)?$")


@dataclass(frozen=True)
class Link:
    line: int
    target: str
    anchor: Optional[str]


def split_lines(text: str) -> list:
    return text.replace("\r\n", "\n").replace("\r", "\n").split("\n")


def _unfenced(lines: list) -> list:
    """Lines with fenced code blocks (fences included) emptied."""
    out, fence = [], None
    for line in lines:
        m = _FENCE_RE.match(line)
        if fence is None:
            if m and not (m.group(1)[0] == "`" and "`" in line[m.end():]):
                fence = m.group(1)
                out.append("")
            else:
                out.append(line)
        else:
            out.append("")
            if m and m.group(1)[0] == fence[0] and len(m.group(1)) >= len(fence) \
                    and not line.strip().strip(fence[0]):
                fence = None
    return out


def _blank_inline(line: str) -> str:
    return _INLINE_CODE_RE.sub(lambda m: " " * len(m.group(0)), line)


def links(text: str) -> list:
    result = []
    for n, line in enumerate(_unfenced(split_lines(text)), 1):
        line = _blank_inline(line)
        raws = [m.group(1) for m in _INLINE_LINK_RE.finditer(line)]
        ref = _REF_DEF_RE.match(line)
        if ref:
            raws.append(ref.group(1))
        for raw in raws:
            if raw.startswith("<") and raw.endswith(">"):
                raw = raw[1:-1]
            if _SCHEME_RE.match(raw):
                continue
            path, hashed, anchor = raw.partition("#")
            path = unquote(path)
            if not path and not anchor:
                continue
            result.append(Link(n, path, anchor if hashed and anchor else None))
    return result


PLACEHOLDERS = ("X.Y.Z", "NNNN", "YYYY", "yyyy", "MM-dd", "MM-DD", "HHmm", "…")


def has_placeholder(text: str) -> bool:
    return any(p in text for p in PLACEHOLDERS)


def is_repo_path(token: str) -> bool:
    if not token or has_placeholder(token) or any(c in token for c in "<>*") or any(c.isspace() for c in token):
        return False
    if "://" in token or token.startswith(("/", "~", "\\")):
        return False
    if re.match(r"^[A-Za-z]:", token):
        return False
    if "/" not in token:
        return False
    last = token.rstrip("/").rsplit("/", 1)[-1]
    if token.endswith("/"):
        return False
    return bool(re.search(r"[^.]\.[A-Za-z][A-Za-z0-9]*$", last))


def code_paths(text: str) -> list:
    result = []
    for n, line in enumerate(_unfenced(split_lines(text)), 1):
        for m in _INLINE_CODE_RE.finditer(line):
            token = m.group(2).strip()
            if is_repo_path(token):
                result.append((n, token))
    return result


def heading_slugs(text: str) -> set:
    slugs, seen = set(), {}
    for line in _unfenced(split_lines(text)):
        m = _HEADING_RE.match(line)
        if not m:
            continue
        base = re.sub(r"[^\w\- ]", "", m.group(1).lower()).replace(" ", "-")
        count = seen.get(base, 0)
        seen[base] = count + 1
        slugs.add(base if count == 0 else f"{base}-{count}")
    return slugs
