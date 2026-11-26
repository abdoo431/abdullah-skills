"""Read-only git helpers for the versioning script. Prints nothing; failures return None or empty values."""
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

from ver_semver import Version


def git(root: Path, *args: str) -> Optional[str]:
    """Run git in root and return stdout, or None when git fails or is missing."""
    env = dict(os.environ, GIT_TERMINAL_PROMPT="0", GIT_OPTIONAL_LOCKS="0")
    try:
        proc = subprocess.run(
            ["git", "--no-pager", "-c", "core.quotepath=off", "-c", "color.ui=false", *args],
            cwd=root, capture_output=True, text=True, encoding="utf-8",
            errors="replace", env=env, stdin=subprocess.DEVNULL,
        )
    except (OSError, ValueError):
        return None
    return proc.stdout if proc.returncode == 0 else None


def _lines(out: Optional[str]) -> list:
    return [line.strip() for line in (out or "").splitlines() if line.strip()]


def is_repo(root: Path) -> bool:
    out = git(root, "rev-parse", "--is-inside-work-tree")
    return out is not None and out.strip() == "true"


def current_branch(root: Path) -> Optional[str]:
    out = git(root, "symbolic-ref", "--quiet", "--short", "HEAD")
    return out.strip() or None if out is not None else None


def branches(root: Path) -> list:
    names = set()
    for ref in _lines(git(root, "for-each-ref", "--format=%(refname)", "refs/heads", "refs/remotes")):
        if ref.startswith("refs/heads/"):
            names.add(ref[len("refs/heads/"):])
        elif ref.startswith("refs/remotes/"):
            rest = ref[len("refs/remotes/"):]
            remote, _, name = rest.partition("/")
            if name and name != "HEAD":
                names.add(name)
    return sorted(names)


def all_tags(root: Path) -> list:
    return _lines(git(root, "tag", "--list"))


def _format_re(tag_format: str) -> re.Pattern:
    before, _, after = tag_format.partition("{version}")
    return re.compile("^" + re.escape(before) + r"(?P<v>\d+\.\d+\.\d+(?:-[0-9A-Za-z.-]+)?)" + re.escape(after) + "$")


def tag_versions(root: Path, tag_format: str) -> list:
    pattern = _format_re(tag_format)
    found = []
    for tag in all_tags(root):
        m = pattern.match(tag)
        if not m:
            continue
        try:
            found.append((tag, Version.parse(m.group("v"))))
        except ValueError:
            continue
    return sorted(found, key=lambda tv: tv[1])


def branches_containing(root: Path, tag: str) -> list:
    out = git(root, "branch", "--all", "--format=%(refname)", "--contains", tag)
    names = set()
    for ref in _lines(out):
        if ref.startswith("refs/heads/"):
            names.add(ref[len("refs/heads/"):])
        elif ref.startswith("refs/remotes/"):
            name = ref[len("refs/remotes/"):].partition("/")[2]
            if name and name != "HEAD":
                names.add(name)
    return sorted(names)


def show(root: Path, ref: str, path: str) -> Optional[str]:
    return git(root, "show", f"{ref}:{path}")


def remote_url(root: Path) -> Optional[str]:
    out = git(root, "remote", "get-url", "origin")
    return out.strip() or None if out is not None else None
