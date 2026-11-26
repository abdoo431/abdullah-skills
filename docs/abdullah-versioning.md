# abdullah-versioning

Owns a project's version number and its releases, in any language. Source: [`skills/abdullah-versioning/SKILL.md`](../skills/abdullah-versioning/SKILL.md).

## What it does

It answers four questions a release by hand keeps raising: what the next version is, which of its three parts goes up, where the project declares its version, and when it is time to release. It reads the changelog's `[Unreleased]` entries to propose the next version, finds every file that declares the version and writes them all at once, and runs the release on the project's own branches: the cut, release candidates, the tag, the GitHub Release, hotfixes, and fixes for older release lines.

The fact that sets it apart: **it decides the number from the changelog, not from commit messages, and it never writes, tags or pushes before you have seen and approved it.** Before `1.0.0`, a release is a finished milestone, so a new feature does not raise the version on its own; `1.0.0` itself is only ever your call.

## When to reach for it

The agent reaches for it on its own when you ask for a release, a version, a tag, a release candidate or a hotfix, and after a pull request merges into the branch where work lands, to say whether a release is due. You can also invoke it by name.

It ends where [abdullah-docs](abdullah-docs.md) begins: `abdullah-docs` writes the `[Unreleased]` entries during normal work; this skill moves them into a version section when a release is cut. Publishing packages (NuGet, PyPI, npm) and deploying stay with your CI.

## Prerequisites

- Python 3.10 or later, for its script. Without it, the setup gives you the one command that installs it, or the skill does the steps by hand and says its checks did not run.
- A project set up with [setup-abdullah-versioning](setup-abdullah-versioning.md), or the skill offers that setup the first time it runs.

## Which part goes up

| Before 1.0.0 | From 1.0.0 |
|---|---|
| A feature-level entry (`Added`, `Changed`, `Deprecated`, `Removed`): MINOR | Something that breaks existing use, or `Removed`: MAJOR |
| Only `Fixed` and `Security`: PATCH | A backward-compatible feature: MINOR |
| A breaking change: still MINOR | Only fixes: PATCH |

It shows the proposal with the entries that decided it, for example "`0.3.0` → `0.4.0`, because `Added`: workspace export", and asks you about any `Changed` entry that might break existing use. The full rules are in [`reference/rules.md`](../skills/abdullah-versioning/reference/rules.md).

## Branch layouts

It works with branch roles, whatever the branches are called (`main`, `master` or any name):

- **`dev` → `staging` → `main`**: work lands on `dev`, a release candidate (`0.2.0-rc.1`) is tried on `staging`, and the release is tagged on `main`.
- **`dev` and `main`**: work lands on `dev`; a release goes from `dev` into `main` and is tagged there.
- **`main` alone**: work lands on `main`; each release is tagged on it.

Pre-releases are `-alpha.N`, `-beta.N` and `-rc.N`; between releases the integration branch declares the next version with `-dev`, which is never tagged. Every flow, back-merges included, is in [`reference/layouts.md`](../skills/abdullah-versioning/reference/layouts.md); hotfixes and older release lines are in [`reference/hotfix.md`](../skills/abdullah-versioning/reference/hotfix.md).

## Where the version lives

`.props` and `.csproj` files, `pyproject.toml` or a Python `__version__`, `package.json` with its lock file, `Cargo.toml` with its lock file, plugin manifests, a `VERSION` file, any other file through a pattern you approve, or only the git tags. Each file keeps every byte except the version, and Python files get the PEP 440 form (`0.2.0rc1`). See [`reference/sources.md`](../skills/abdullah-versioning/reference/sources.md).

## It's working if

- Before a release, the agent shows you the proposed version and the changelog entries behind it, and waits.
- After a release, every declared version agrees, the changelog has a dated section for it, and the tag points at the release commit.
- No push, pull request, tag push or GitHub Release happens without your approval of that step.
- `python <skill>/scripts/version.py check` exits 0 on each long-lived branch.
- No tag ends in `-dev`.

## Where it fits

It completes [abdullah-docs](abdullah-docs.md): the fourth of its four questions, "when did it ship, and in which version?", is answered by the tags and changelog sections this skill writes. [setup-abdullah-versioning](setup-abdullah-versioning.md) is the command that starts its setup.
