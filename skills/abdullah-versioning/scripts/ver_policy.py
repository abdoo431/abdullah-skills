"""Read the abdullah-versioning settings block from a project's release policy."""
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

BLOCK = "abdullah-versioning"
AGENT_SECTION_HEADING = "## Versioning (abdullah-versioning)"
POLICY_PLACES = ("docs/RELEASING.md", "RELEASING.md", "CONTRIBUTING.md", "docs/DOCUMENTATION.md")
LAYOUTS = ("dev-staging-main", "dev-main", "main")

_BLOCK_RE = re.compile(r"^```abdullah-versioning[ \t]*\r?\n(.*?)^```", re.M | re.S)
_UNSET = object()


@dataclass
class Settings:
    layout: Optional[str] = None
    production: str = "main"
    staging: str = "staging"
    integration: str = "dev"
    sources: list = field(default_factory=list)
    tag: str = "v{version}"
    changelog: str = "CHANGELOG.md"
    dev_suffix: Optional[str] = "dev"
    pre_releases: list = field(default_factory=lambda: ["rc"])
    release_branch: str = "release/{version}"
    hotfix_branch: str = "hotfix/{version}-{name}"
    support_branch: str = "support/{major}.{minor}.x"
    first_version: str = "0.1.0"


def _csv(value: str) -> list:
    return [v.strip() for v in value.split(",") if v.strip()]


def _read(path: Path) -> str:
    return Path(path).read_bytes().decode("utf-8", errors="replace").lstrip("﻿")


def read_settings(policy: Optional[Path]) -> Settings:
    s = Settings()
    if policy is None:
        return s
    block = _BLOCK_RE.search(_read(policy))
    dev_suffix = _UNSET
    if block:
        for raw in block.group(1).splitlines():
            key, sep, value = raw.partition(":")
            key, value = key.strip().lower(), value.strip()
            if not sep or not value:
                continue
            if key == "layout":
                if value not in LAYOUTS:
                    raise ValueError(f"layout {value!r} is not one of: {', '.join(LAYOUTS)}")
                s.layout = value
            elif key in ("production", "staging", "integration", "tag", "changelog"):
                setattr(s, key, value)
            elif key == "sources":
                s.sources = _csv(value)
            elif key == "dev-suffix":
                dev_suffix = None if value.lower() == "none" else value
            elif key == "pre-releases":
                s.pre_releases = [] if value.lower() == "none" else _csv(value)
            elif key in ("release-branch", "hotfix-branch", "support-branch", "first-version"):
                setattr(s, key.replace("-", "_"), value)
    if dev_suffix is _UNSET:
        s.dev_suffix = None if s.layout == "main" else "dev"
    else:
        s.dev_suffix = dev_suffix
    return s


def find_policy(root: Path) -> Optional[Path]:
    root = Path(root)
    for rel in POLICY_PLACES:
        path = root / rel
        if path.is_file() and _BLOCK_RE.search(_read(path)):
            return path
    return None
