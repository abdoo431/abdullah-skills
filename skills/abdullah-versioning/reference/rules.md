# Versioning rules

These are the skill's defaults. The project's release policy wins over them.

## The scheme

[Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html): `MAJOR.MINOR.PATCH`, with an optional pre-release label after a hyphen (`0.2.0-rc.1`). Tags and the changelog always use this form. Python sources use the PEP 440 form of the same version ([sources.md](sources.md)).

## Which part goes up

`version.py plan` reads the entries under `[Unreleased]` and proposes the part. You decide the `Changed` entries it lists under `judge:`.

**Before 1.0.0** (`0.MINOR.PATCH`):

| `[Unreleased]` holds | Next version |
|---|---|
| Any `Added`, `Changed`, `Deprecated` or `Removed` entry | MINOR: `0.3.0` → `0.4.0` |
| Only `Fixed` and `Security` entries | PATCH: `0.3.0` → `0.3.1` |

A breaking change before 1.0.0 raises MINOR, not MAJOR. A minor release before 1.0.0 marks a finished milestone, not each new feature: suggest one when the owner says the milestone is done.

**From 1.0.0:**

| `[Unreleased]` holds | Next version |
|---|---|
| A `Removed` entry, or any entry that breaks existing use (a public API, a data format, a command, an event name) | MAJOR |
| An `Added` or `Deprecated` entry, or a `Changed` entry that breaks nothing | MINOR |
| Only `Fixed` and `Security` entries | PATCH |

A `Changed` entry that breaks existing use: run `plan --major`. A subsection outside Keep a Changelog's six counts as MINOR and is listed for your judgment.

## The first version and 1.0.0

- A project's first release is `0.1.0`, unless the owner chose another during the setup (`first-version` in the policy).
- `1.0.0` means the project is declared ready for production use. Only the owner declares it; the script refuses it without `--first-major`, which you pass only after the owner's word.
- A version a project template wrote is not a release: a `.csproj` with no `<Version>`, or a fresh `pyproject.toml` saying `0.1.0`. Only a tag or a released changelog section counts.

## Pre-releases

A pre-release is a version published for testing before the release. `N` counts the attempts within one stage.

| Label | Means | Who tries it | What may still go in |
|---|---|---|---|
| `-alpha.N` | The release's features are still being built | The owner or the team | Features and large changes |
| `-beta.N` | Every feature of the release is in | People outside the team | Fixes only |
| `-rc.N` | Release candidate: it ships unchanged unless a serious defect turns up | A last trial, close to production | Fixes for serious defects only |

- Order: `0.2.0-alpha.1` < `-alpha.2` < `-beta.1` < `-rc.1` < `-rc.2` < `0.2.0`.
- Stages may be skipped. The default is `rc` alone; use `alpha` and `beta` when the owner asks or the policy's `pre-releases` names them.
- A stage never goes back: after `rc.1`, a serious defect gives `rc.2`, never a `beta`. The script refuses a step back.
- `N` starts at 1 in each stage. `version.py prepare X.Y.Z --pre rc` declares the first; `version.py declare X.Y.Z-rc.2` the next.
- A pre-release tag points at a commit whose version files declare exactly that pre-release: tag right after the commit that declared it.

## The `-dev` marker

On the integration branch, between releases, the version files declare the next version with `-dev`: after `v0.4.0`, `dev` declares `0.5.0-dev`. Every build is then told apart from the release before it, and a version without a label always has a tag.

`-dev` is never tagged or published: SemVer sorts `0.5.0-dev` above `0.5.0-alpha.1` and `0.5.0-beta.1` although it is older. The `main` layout has no `-dev` by default (`dev-suffix: none`).

## The `Fixed`-into-`Added` fold

At the cut, a `Fixed` entry for something first added in this same release folds into its `Added` entry: the release never had the defect. `prepare` lists the candidates under `fold:`; edit the new section yourself before committing, and keep `Fixed` entries about earlier releases. This is the only hand edit of a version section, made on the release branch before its tag exists.
