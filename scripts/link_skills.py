"""Maintainer only: link this working copy's skills into local agent skill folders.

Each skills/<name> folder is linked as <dest>/<name>: a directory junction on Windows,
a symbolic link elsewhere. An existing link is replaced; a real folder or file is never
touched, and neither is a link to another folder. --remove deletes only links that
point to this repository's skills.

Exit codes: 0 done, 1 a target was refused or failed, 2 usage error (nothing is changed).
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
    """True for a symbolic link, or a junction on Windows (os.path.islink misses those).

    Other reparse points, such as OneDrive placeholders, are real folders, not links.
    """
    if os.path.islink(path):
        return True
    if os.name != "nt":
        return False
    try:
        st = os.lstat(path)
    except OSError:
        return False
    if not st.st_file_attributes & stat.FILE_ATTRIBUTE_REPARSE_POINT:
        return False
    return st.st_reparse_tag in (stat.IO_REPARSE_TAG_MOUNT_POINT, stat.IO_REPARSE_TAG_SYMLINK)


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


def points_to(link: Path, source: Path) -> bool:
    """True when the link resolves to source (this repository's skill folder)."""
    try:
        return link.resolve() == source.resolve()
    except OSError:
        return False


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

    failed = False
    for dest in dests:
        for name in names:
            target, source = dest / name, SKILLS / name
            where = target.as_posix()
            exists = os.path.lexists(target)
            if exists and not is_link(target):
                print(f"link_skills.py: error: {where} is not a link; left it in place", file=sys.stderr)
                failed = True
                continue
            if exists and not points_to(target, source):
                if args.remove:
                    print(f"left {where}: it links to another folder, not this repository")
                else:
                    print(f"link_skills.py: error: {where} links to another folder; left it in place",
                          file=sys.stderr)
                    failed = True
                continue
            try:
                if args.remove:
                    if not exists:
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
                if exists:
                    remove_link(target)
                make_link(source, target)
                print(f"linked {name} -> {dest.as_posix()}")
            except OSError as exc:
                print(f"error: {where}: {exc.strerror or exc}", file=sys.stderr)
                failed = True
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
