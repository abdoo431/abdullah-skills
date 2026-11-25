"""Read the documentation policy settings."""
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

AGENT_SECTION_HEADING = "## Documentation (abdullah-docs)"

_PROFILE_RE = re.compile(r"^[ \t]*Documentation profile:[ \t]*(.*)$", re.M | re.I)
_BLOCK_RE = re.compile(r"^```abdullah-docs[ \t]*\r?\n(.*?)^```", re.M | re.S)
_DOC_HEADING_RE = re.compile(r"^##\s+Documentation\s*$", re.M)


@dataclass
class Settings:
    profile: str = "lean"
    adr_dir: str = "docs/adr"
    changelog: str = "CHANGELOG.md"
    base: Optional[str] = None
    history: list = field(default_factory=list)
    pairs: list = field(default_factory=list)
    examples: list = field(default_factory=list)
    specs: str = "docs/superpowers/specs"
    plans: str = "docs/superpowers/plans"


def _csv(value: str) -> list:
    return [v.strip() for v in value.split(",") if v.strip()]


def read_settings(policy: Optional[Path]) -> Settings:
    s = Settings()
    if policy is None:
        return s
    text = Path(policy).read_text(encoding="utf-8", errors="replace")
    m = _PROFILE_RE.search(text)
    if m:
        words = m.group(1).split()
        value = words[0].strip("`*_.,;:").lower() if words else ""
        if value:
            s.profile = value
    block = _BLOCK_RE.search(text)
    if not block:
        return s
    for raw in block.group(1).splitlines():
        key, sep, value = raw.partition(":")
        value = value.strip()
        if not sep or not value:
            continue
        key = key.strip().lower()
        if key == "adr-dir":
            s.adr_dir = value
        elif key == "changelog":
            s.changelog = value
        elif key == "base":
            s.base = value
        elif key == "specs":
            s.specs = value
        elif key == "plans":
            s.plans = value
        elif key == "history":
            s.history = _csv(value)
        elif key == "examples":
            s.examples = _csv(value)
        elif key == "pairs":
            s.pairs = [
                (a.strip(), b.strip())
                for a, _, b in (p.partition(":") for p in _csv(value))
                if a.strip() and b.strip()
            ]
    return s


def find_policy(root: Path) -> Optional[Path]:
    root = Path(root)
    for rel in ("docs/DOCUMENTATION.md", "DOCUMENTATION.md"):
        if (root / rel).is_file():
            return root / rel
    contributing = root / "CONTRIBUTING.md"
    if contributing.is_file():
        text = contributing.read_text(encoding="utf-8", errors="replace")
        if _DOC_HEADING_RE.search(text):
            return contributing
    return None
