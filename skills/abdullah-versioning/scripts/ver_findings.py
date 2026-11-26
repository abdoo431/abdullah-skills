"""Findings shared by the abdullah-versioning scripts."""
import sys
from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class Finding:
    path: str
    line: int
    severity: str
    kind: str
    message: str


def use_utf8_output() -> None:
    """Print UTF-8 whatever the console code page is, replacing what cannot be encoded."""
    for stream in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure:
            reconfigure(encoding="utf-8", errors="replace")


def warning(path: str, line: int, kind: str, message: str) -> Finding:
    return Finding(path, line, "warning", kind, message)


def error(path: str, line: int, kind: str, message: str) -> Finding:
    return Finding(path, line, "error", kind, message)


def format_finding(f: Finding) -> str:
    return f"{f.path}:{f.line}: {f.severity}: {f.kind}: {f.message}"


def exit_code(findings: Iterable[Finding]) -> int:
    return 1 if any(f.severity == "error" for f in findings) else 0
