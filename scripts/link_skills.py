"""Maintainer only: link this working copy's skills into local agent skill folders.

Each skills/<name> folder is linked as <dest>/<name>: a directory junction on Windows,
a symbolic link elsewhere. An existing link is replaced; a real folder or file is never
touched. --remove deletes only the links this script would create.

Exit codes: 0 done, 1 a target was refused, 2 usage error (nothing is changed).
"""
import argparse
import os
import stat
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
SKILLS = REPO / "skills"
DEFAULT_DESTS = (Path.home() / ".claude" / "skills", Path.home() / ".agents" / "skills")


def is_link(path: Path) -> bool:
    """True for a symbolic link, or a junction on Windows (os.path.islink misses those)."""
    if os.path.islink(path):
        return True
    if os.name != "nt":
        return False
    try:
        attributes = os.lstat(path).st_file_attributes
    except OSError:
        return False
    return bool(attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT)


def make_link(source: Path, target: Path) -> None:
    if os.name == "nt":
        import _winapi
        _winapi.CreateJunction(str(source), str(target))
    else:
        os.symlink(source, target, target_is_directory=True)


def remove_link(target: Path) -> None:
    # os.rmdir removes a junction or directory link without touching what it points to;
    # shutil.rmtree would delete the skill's files through it.
    if os.name == "nt":
        try:
            os.rmdir(target)
        except NotADirectoryError:
            os.unlink(target)
    else:
        os.unlink(target)


def _inside_repo(dest: Path) -> bool:
    resolved = dest.resolve()
    return resolved == REPO or REPO in resolved.parents


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--dest", action="append", metavar="DIR",
                    help="agent skill folder to link into; repeatable "
                         "(default: ~/.claude/skills and ~/.agents/skills)")
    ap.add_argument("--dry-run", action="store_true", help="print what would happen, change nothing")
    ap.add_argument("--remove", action="store_true", help="remove the links instead of creating them")
    args = ap.parse_args(argv)

    dests = [Path(d).expanduser().absolute() for d in args.dest] if args.dest else list(DEFAULT_DESTS)
    for dest in dests:
        if _inside_repo(dest):
            print(f"link_skills.py: error: {dest.as_posix()} is inside the repository", file=sys.stderr)
            return 2
    names = sorted(p.parent.name for p in SKILLS.glob("*/SKILL.md"))

    refused = False
    for dest in dests:
        for name in names:
            target = dest / name
            if os.path.lexists(target) and not is_link(target):
                print(f"link_skills.py: error: {target.as_posix()} is not a link; left it in place",
                      file=sys.stderr)
                refused = True
                continue
            if args.remove:
                if not os.path.lexists(target):
                    continue
                if args.dry_run:
                    print(f"would remove {name} from {dest.as_posix()}")
                else:
                    remove_link(target)
                    print(f"removed {name} from {dest.as_posix()}")
                continue
            if args.dry_run:
                print(f"would link {name} -> {dest.as_posix()}")
                continue
            dest.mkdir(parents=True, exist_ok=True)
            if os.path.lexists(target):
                remove_link(target)
            make_link(SKILLS / name, target)
            print(f"linked {name} -> {dest.as_posix()}")
    return 1 if refused else 0


if __name__ == "__main__":
    sys.exit(main())
