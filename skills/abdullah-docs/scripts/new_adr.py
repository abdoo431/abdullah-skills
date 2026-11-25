"""Create the next-numbered ADR and add it to the ADR index.

Prints only the new file's repository path on stdout; warnings go to stderr.
Exit codes: 0 done, 2 usage error (nothing is written).
"""
import argparse
import os
import re
import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import docs_adr  # noqa: E402
import docs_findings  # noqa: E402
import docs_git  # noqa: E402
import docs_policy  # noqa: E402

TEMPLATES = Path(__file__).resolve().parent.parent / "templates"
NEW_INDEX = "# Architecture Decision Records\n\n| ADR | Decision | Status |\n|-----|----------|--------|\n"


def _read(path: Path) -> str:
    return path.read_bytes().decode("utf-8", errors="replace")


def _fail(message: str) -> int:
    print(f"new_adr.py: error: {message}", file=sys.stderr)
    return 2


def _warn_base(adr_dir: str, message: str) -> None:
    print(docs_findings.format_finding(docs_findings.warning(adr_dir, 1, "base", message)), file=sys.stderr)


def _numbered_h1(adr_dir: Path, local: list) -> bool:
    if not local:
        return True
    latest = max(local, key=lambda f: f.number)
    for line in _read(adr_dir / latest.name).splitlines():
        if line.startswith("# "):
            return re.match(r"#\s+\d", line) is not None
    return True


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--root", default=".")
    ap.add_argument("--title", required=True)
    ap.add_argument("--adr-dir")
    ap.add_argument("--base")
    ap.add_argument("--policy")
    ap.add_argument("--short", action="store_true")
    args = ap.parse_args(argv)

    root = Path(args.root).resolve()
    title = " ".join(args.title.split())
    if not title:
        return _fail("--title must not be empty")

    policy = None
    if args.policy:
        policy = Path(args.policy)
        if not policy.is_absolute() and (root / policy).exists():
            policy = root / policy
    else:
        policy = docs_policy.find_policy(root)
    try:
        settings = docs_policy.read_settings(policy)
    except (FileNotFoundError, OSError):
        return _fail(f"policy file not found: {args.policy}")

    adr_rel = (args.adr_dir or settings.adr_dir).replace("\\", "/").strip("/") or "."
    adr_dir = root / adr_rel
    local_names = sorted(os.listdir(adr_dir)) if adr_dir.is_dir() else []

    odd = docs_adr.unrecognised_adrs(local_names)
    if odd:
        return _fail(f"{adr_rel} holds ADR-like files this script cannot number: {', '.join(odd)}")

    slug = docs_adr.slugify(title)
    if not slug:
        return _fail("--title needs at least one letter or digit")

    base = args.base or settings.base or docs_git.default_base(root)
    base_names: list[str] = []
    if base and docs_git.is_repo(root) and docs_git.ref_exists(root, base):
        base_names = docs_git.files_at(root, base, adr_rel)
    elif base:
        _warn_base(adr_rel, f"base '{base}' does not exist here (fetch it?); numbering from local ADRs only")
    else:
        _warn_base(adr_rel, "no base branch found; numbering from local ADRs only")

    local = docs_adr.adr_files(local_names)
    number = docs_adr.next_number(local, docs_adr.adr_files(base_names))
    width = docs_adr.number_width(local or docs_adr.adr_files(base_names))
    number_s = str(number).zfill(width)
    name = f"{number_s}-{slug}.md"

    index_path = adr_dir / "README.md"
    index_rel = f"{adr_rel}/README.md" if adr_rel != "." else "README.md"
    index_text = _read(index_path) if index_path.is_file() else NEW_INDEX
    try:
        new_index = docs_adr.insert_index_row(index_text, number_s, name, title)
    except docs_adr.IndexFormatError:
        return _fail(f"{index_rel} is neither a table nor a list of ADR links; add the row by hand or fix the index")

    if args.short:
        template_path = TEMPLATES / "adr-short.md"
    else:
        template_path = docs_adr.project_template(adr_dir) or TEMPLATES / "adr-full.md"
    body = docs_adr.render(_read(template_path), number_s, title, date.today().isoformat(),
                           _numbered_h1(adr_dir, local))

    adr_dir.mkdir(parents=True, exist_ok=True)
    (adr_dir / name).write_bytes(body.encode("utf-8"))
    index_path.write_bytes(new_index.encode("utf-8"))
    print(f"{adr_rel}/{name}" if adr_rel != "." else name)
    return 0


if __name__ == "__main__":
    sys.exit(main())
