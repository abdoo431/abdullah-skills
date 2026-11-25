"""Git helpers for the abdullah-docs scripts. Prints nothing; failures return None or empty values."""
import fnmatch
import os
import re
import subprocess
from pathlib import Path

_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
_SKIP_DIRS = {".git", "node_modules"}


def git(root: Path, *args: str) -> str | None:
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


def _lines(out: str | None) -> list[str]:
    return [line for line in (out or "").splitlines() if line]


def is_repo(root: Path) -> bool:
    out = git(root, "rev-parse", "--is-inside-work-tree")
    return out is not None and out.strip() == "true"


def default_base(root: Path) -> str | None:
    out = git(root, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    return out.strip() or None if out is not None else None


def ref_exists(root: Path, ref: str) -> bool:
    return git(root, "rev-parse", "--verify", "--quiet", f"{ref}^{{commit}}") is not None


def merge_base(root: Path, base: str) -> str | None:
    out = git(root, "merge-base", base, "HEAD")
    return out.strip() or None if out is not None else None


def _comparison_point(root: Path, base: str | None) -> str | None:
    """The merge base when computable, else HEAD when it exists, else None."""
    if base:
        mb = merge_base(root, base)
        if mb:
            return mb
    return "HEAD" if ref_exists(root, "HEAD") else None


def _untracked(root: Path) -> list[str]:
    return _lines(git(root, "ls-files", "--others", "--exclude-standard"))


def changed_files(root: Path, base: str | None) -> set[str]:
    """Files differing from the merge base (or HEAD) in the working tree, plus untracked files."""
    if not is_repo(root):
        return set()
    files = set(_untracked(root))
    point = _comparison_point(root, base)
    if point:
        files.update(_lines(git(root, "diff", "--no-color", "--no-ext-diff", "--name-only", "--relative", point)))
    return files


def added_lines(root: Path, base: str | None, path: str) -> set[int]:
    """Line numbers in the working-tree file added since the merge base; an untracked file is all added."""
    if not is_repo(root):
        return set()
    if path in _untracked(root):
        try:
            text = (Path(root) / path).read_text(encoding="utf-8", errors="replace")
        except OSError:
            return set()
        return set(range(1, len(text.splitlines()) + 1))
    point = _comparison_point(root, base)
    if not point:
        return set()
    out = git(root, "diff", "--no-color", "--no-ext-diff", "--unified=0", "--ignore-cr-at-eol", "--relative", point, "--", path)
    added: set[int] = set()
    for line in (out or "").splitlines():
        m = _HUNK.match(line)
        if m:
            start = int(m.group(1))
            count = int(m.group(2)) if m.group(2) is not None else 1
            added.update(range(start, start + count))
    return added


def files_at(root: Path, ref: str, directory: str) -> list[str]:
    directory = directory.strip("/")
    out = git(root, "ls-tree", "--name-only", ref, f"{directory}/")
    return [line.rsplit("/", 1)[-1] for line in _lines(out)]


def tracked_files(root: Path, pattern: str) -> list[str]:
    """Tracked files matching a git pathspec glob; walks the folder when not a repository."""
    if is_repo(root):
        return sorted(_lines(git(root, "ls-files", "--", pattern)))
    root = Path(root)
    found = []
    for dirpath, dirnames, filenames in os.walk(root):
        dirnames[:] = [d for d in dirnames if d not in _SKIP_DIRS]
        for name in filenames:
            rel = (Path(dirpath) / name).relative_to(root).as_posix()
            if fnmatch.fnmatch(rel, pattern):
                found.append(rel)
    return sorted(found)


def commits_since(root: Path, base: str | None) -> list[str]:
    """Full commit messages from the merge base to HEAD, oldest first."""
    mb = merge_base(root, base) if base else None
    if not mb:
        return []
    out = git(root, "log", "--reverse", "--format=%B%x00", f"{mb}..HEAD")
    return [m.strip() for m in (out or "").split("\0") if m.strip()]
