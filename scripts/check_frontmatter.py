"""Check that every skills/*/SKILL.md has parseable front matter."""
import argparse
import sys
from pathlib import Path


def _front_matter_lines(text):
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for i in range(1, len(lines)):
        if lines[i].strip() == "---":
            return lines[1:i]
    return None


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value.strip()


def check_skill(path: Path) -> list[str]:
    """Return a list of problem messages for one SKILL.md (empty when clean)."""
    path = Path(path)
    text = path.read_bytes().decode("utf-8", errors="replace").lstrip("\ufeff")
    block = _front_matter_lines(text)
    if block is None:
        return ["no front matter block between two `---` lines"]

    problems = []
    fields = {}
    for line in block:
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        key, sep, value = line.partition(":")
        if not sep:
            problems.append(f"line is not `key: value`: {line.strip()}")
            continue
        key, value = key.strip(), value.strip()
        fields[key] = value
        if value and value[0] not in "\"'" and ": " in value:
            problems.append(f"`{key}` contains ': ' and must be quoted")

    for required in ("name", "description"):
        if not _unquote(fields.get(required, "")):
            problems.append(f"missing `{required}`")

    name = _unquote(fields.get("name", ""))
    if name and name != path.parent.name:
        problems.append(f"name `{name}` does not match folder `{path.parent.name}`")
    return problems


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", default=".", help="repository root")
    args = parser.parse_args(argv)
    root = Path(args.root).resolve()

    skills_dir = root / "skills"
    if not skills_dir.is_dir():
        print(f"skills folder not found: {skills_dir.as_posix()}", file=sys.stderr)
        return 2

    failed = False
    for skill in sorted(skills_dir.rglob("SKILL.md")):
        rel = skill.relative_to(root).as_posix()
        for problem in check_skill(skill):
            print(f"{rel}: {problem}")
            failed = True
    if failed:
        return 1
    print("All SKILL.md front matter parses.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
