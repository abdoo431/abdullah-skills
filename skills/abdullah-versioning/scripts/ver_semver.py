"""Semantic Versioning 2.0.0: parse, order, bump, pre-release numbering and PEP 440 forms."""
import re
from dataclasses import dataclass
from functools import total_ordering

_NUM = r"(0|[1-9]\d*)"
_IDENT = r"(?:0|[1-9]\d*|\d*[A-Za-z-][0-9A-Za-z-]*)"
_SEMVER_RE = re.compile(
    rf"^{_NUM}\.{_NUM}\.{_NUM}(?:-({_IDENT}(?:\.{_IDENT})*))?(?:\+[0-9A-Za-z-]+(?:\.[0-9A-Za-z-]+)*)?$"
)
_PEP440_RE = re.compile(
    r"^(\d+)\.(\d+)\.(\d+)"
    r"(?:[-_.]?(a|alpha|b|beta|rc|c)[-_.]?(\d+))?"
    r"(?:[-_.]?dev[-_.]?(\d*))?$",
    re.I,
)
STAGES = ("alpha", "beta", "rc")
_PEP440_STAGE = {"alpha": "a", "beta": "b", "rc": "rc"}
_FROM_PEP440_STAGE = {"a": "alpha", "alpha": "alpha", "b": "beta", "beta": "beta", "rc": "rc", "c": "rc"}


def _ident(text: str):
    return int(text) if text.isdigit() else text


@total_ordering
@dataclass(frozen=True)
class Version:
    major: int
    minor: int
    patch: int
    pre: tuple = ()

    @classmethod
    def parse(cls, text: str) -> "Version":
        m = _SEMVER_RE.match(text.strip()) if isinstance(text, str) else None
        if not m:
            raise ValueError(f"{text!r} is not a semantic version X.Y.Z[-pre]")
        pre = tuple(_ident(p) for p in m.group(4).split(".")) if m.group(4) else ()
        return cls(int(m.group(1)), int(m.group(2)), int(m.group(3)), pre)

    def __str__(self) -> str:
        core = f"{self.major}.{self.minor}.{self.patch}"
        return f"{core}-{'.'.join(str(p) for p in self.pre)}" if self.pre else core

    def _key(self):
        # SemVer §11: a version without pre-release identifiers sorts above any with them;
        # numeric identifiers sort below alphanumeric ones; a shorter list sorts first.
        if not self.pre:
            return (self.major, self.minor, self.patch, 1, ())
        idents = tuple((0, p, "") if isinstance(p, int) else (1, 0, p) for p in self.pre)
        return (self.major, self.minor, self.patch, 0, idents)

    def __lt__(self, other: "Version") -> bool:
        if not isinstance(other, Version):
            return NotImplemented
        return self._key() < other._key()

    @property
    def is_final(self) -> bool:
        return not self.pre

    @property
    def stage(self):
        return str(self.pre[0]) if self.pre else None

    @property
    def final(self) -> "Version":
        return Version(self.major, self.minor, self.patch)


def bump(v: Version, part: str) -> Version:
    if part == "major":
        return Version(v.major + 1, 0, 0)
    if part == "minor":
        return Version(v.major, v.minor + 1, 0)
    if part == "patch":
        return Version(v.major, v.minor, v.patch + 1)
    raise ValueError(f"unknown part {part!r}: use major, minor or patch")


def next_pre(target: Version, stage: str, existing) -> Version:
    """target's -stage.N, N one more than the highest existing pre-release of that stage."""
    if stage not in STAGES:
        raise ValueError(f"{stage!r} is not a pre-release stage: use alpha, beta or rc")
    final = target.final
    same = [v for v in existing if v.final == final and not v.is_final]
    rank = STAGES.index(stage)
    later = [v for v in same if v.stage in STAGES and STAGES.index(v.stage) > rank]
    if later:
        raise ValueError(f"{max(later)} already exists: a pre-release never goes back to {stage}")
    numbers = [v.pre[1] for v in same if v.stage == stage and len(v.pre) > 1 and isinstance(v.pre[1], int)]
    return Version(final.major, final.minor, final.patch, (stage, max(numbers, default=0) + 1))


def to_pep440(v: Version) -> str:
    core = f"{v.major}.{v.minor}.{v.patch}"
    if v.is_final:
        return core
    if v.stage == "dev":
        return f"{core}.dev0"
    if v.stage in _PEP440_STAGE and len(v.pre) == 2 and isinstance(v.pre[1], int):
        return f"{core}{_PEP440_STAGE[v.stage]}{v.pre[1]}"
    raise ValueError(f"{v} has no PEP 440 form")


def from_pep440(text: str) -> Version:
    try:
        return Version.parse(text)
    except ValueError:
        pass
    m = _PEP440_RE.match(text.strip())
    if not m:
        raise ValueError(f"{text!r} is not a version")
    major, minor, patch = int(m.group(1)), int(m.group(2)), int(m.group(3))
    if m.group(4):
        return Version(major, minor, patch, (_FROM_PEP440_STAGE[m.group(4).lower()], int(m.group(5))))
    if m.group(6) is not None:
        return Version(major, minor, patch, ("dev",))
    return Version(major, minor, patch)
