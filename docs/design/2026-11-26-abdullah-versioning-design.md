# abdullah-versioning: design

- **Status:** Approved by the owner on 2026-11-26
- **Date:** 2026-11-26
- **Companion skills:** `setup-abdullah-versioning` (this design); `abdullah-docs`, which writes the `[Unreleased]` entries this skill releases ([its design, §10](2026-11-25-abdullah-docs-design.md#10-boundaries-with-other-skills))
- **Repository:** `abdoo431/abdullah-skills`, as a third and fourth folder under `skills/` ([ADR 0001](../../.agents/adr/0001-skills-and-install-routes.md))

## 1. Intent

An agent skill that owns a project's version number and its releases, in any language. It answers the fourth of the four questions `abdullah-docs` keeps in place: **when did this ship, and in which version?**

### Why it is needed

The owner releases by hand, and each release raises the same four questions:

1. **What is the next version number?**
2. **Which of the three parts goes up**, major, minor or patch?
3. **Where is the version stored** in this project, and in how many places?
4. **When is it time to release** at all?

A release by hand also touches several files that must agree. In the owner's earlier private project (a .NET backend with a web front end, seven releases from `v0.1.0` to `v0.7.0`), one release touched five places: the changelog section and its links, `Directory.Build.props`, `package.json`, `package-lock.json` twice, and a test that repeated the version. The project later wrote a release script that edits them all and refuses a bad state before writing anything; that script, its ADR and its runbook are the prior art for this skill (§6, §9).

The skill must work on projects that already have releases, and on new ones it numbers from the start.

## 2. Goals, non-goals, anti-goals

**Goals**

1. Decide the next version, and say which part goes up and why, from the project's `[Unreleased]` changelog entries.
2. Find where a project declares its version, in any language, and keep every place in agreement.
3. Tell a new project from one with releases, and adopt an existing project's versions, tag format and branches.
4. Run the release on the project's branch layout: `dev` → `staging` → `main`, `dev` and `main`, or `main` alone, whatever the branches are called.
5. Support pre-releases (`-alpha.N`, `-beta.N`, `-rc.N`), hotfixes, and fixes for older release lines.
6. Suggest a release when one is due, and stay quiet when it is not.

**Non-goals**

- **Publishing packages** (NuGet, PyPI, npm, crates.io) and deploying. A release ends with the tag and, on GitHub, a GitHub Release (C14). Publishing is the project's CI or the owner's command.
- **Version schemes other than SemVer**, such as CalVer (`2026.11`). The setup detects them and stops (§6.3).
- **Monorepos with independently versioned packages.** The setup detects several unrelated versions and stops. One version shared by several files is supported.
- **Writing changelog entries during normal work.** `abdullah-docs` does that.
- **Running in a project's CI.** The script stays inside the skill, as `abdullah-docs` decided (its D4).

**Anti-goals** (it works, but it failed)

- It picks a version, writes a file, creates a tag or pushes without the owner seeing and approving it.
- It declares `1.0.0` on its own.
- It guesses when tags, files and the changelog disagree, instead of stopping and asking.
- It rewrites a released changelog section, or moves or deletes an existing tag.
- It replaces a project's existing branch names, tag format or release habits with its own defaults.

## 3. Constraints

- **Any language.** The version may live in XML, TOML, JSON, a Python or C# source file, a plain file, or only in git tags.
- **Harness-neutral text**, as in the `abdullah-docs` design §3: no tool of one agent named in procedure text; a dependency on another skill reads "call the Skill tool with `<name>`".
- **Scripts:** Python 3.10 or later, the standard library only, runnable from any folder (the repository's rule). Python 3.10 has no TOML reader; the script edits version lines as text anyway, to keep each file's formatting (§9.2).
- **Real folders, no symbolic links**, because plugin installers drop them.
- **Nothing private** in committed files: the prior-art project is named only as the owner's earlier private project.

## 4. Approaches

Four ways to build it were considered. The owner picked **A**.

| | Approach | Trade-off |
|---|---|---|
| **A** | **One skill plus one standard-library Python script inside it.** The script does what must not go wrong: read the versions, propose the next one, move the changelog, write every version file, refuse a bad state. The agent does what needs judgment and approval: weigh `Changed` entries, show the number, run branches, pull requests and tags. | Deterministic and tested, like `abdullah-docs`; the prior-art script shows it works. Costs more code, and each new file format needs a small reader and writer. |
| B | Instructions only; the agent edits the files by hand from a checklist. | Smallest. But it is the manual release the owner wants to stop, done by an agent: no tests, and version files can drift apart unnoticed. |
| C | The setup copies a release script into each project. | Works without the skill and in CI. Copies drift, every fix must be carried to every project, and it breaks `abdullah-docs` D4 (scripts stay in the skill). |
| D | Wrap existing tools: release-please, semantic-release, GitVersion, MinVer, bump-my-version. | Each serves one ecosystem or needs CI; most bump from commit messages, which contradicts "a pre-1.0 minor is a milestone" (§5.2). The prior-art project rejected them for the same reasons. |

**Python or JavaScript.** The owner asked whether JavaScript would serve users without Python. It would not: Node.js is not preinstalled on any operating system either, the Claude Code installer does not need it, Python's standard library reads XML (and TOML from 3.11) where Node's reads only JSON, and the repository's scripts, tests and CI are Python. The owner kept Python. A project without Python gets one install command from the setup, or the steps done by hand with the script's checks reported as not run (§6.3).

## 5. Versioning rules

These are the skill's defaults. A project's written release policy wins over them, as in `abdullah-docs` (its C1).

### 5.1 Scheme

[Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html): `MAJOR.MINOR.PATCH`, with an optional pre-release label after a hyphen.

### 5.2 Which part goes up

The script reads the entries under `[Unreleased]` in the changelog and proposes the part; the agent decides the `Changed` entries and shows the result with its reasons.

**Before 1.0.0** (`0.MINOR.PATCH`):

| `[Unreleased]` holds | Next version |
|---|---|
| Any `Added`, `Changed`, `Deprecated` or `Removed` entry | MINOR: `0.3.0` → `0.4.0` |
| Only `Fixed` and `Security` entries | PATCH: `0.3.0` → `0.3.1` |

A breaking change before 1.0.0 raises MINOR, not MAJOR, as SemVer allows for `0.y.z`. Before 1.0.0 a minor release marks a finished milestone, not each new feature, which is why the release suggestion (§5.6) waits for one.

**From 1.0.0:**

| `[Unreleased]` holds | Next version |
|---|---|
| A `Removed` entry, or any entry that breaks existing use (a public API, a data format, a command, an event name) | MAJOR |
| An `Added` or `Deprecated` entry, or a `Changed` entry that breaks nothing | MINOR |
| Only `Fixed` and `Security` entries | PATCH |

**`Changed` entries need judgment.** The script flags each one; the agent reads it and decides whether it breaks existing use. When unsure, it asks the owner.

**The proposal is shown before anything is written**, with the entries that decided it, for example: "`0.3.0` → `0.4.0`, because `Added`: workspace export". The owner approves or changes it.

### 5.3 The first version and 1.0.0

- A project's first release is `0.1.0`, unless the owner chooses `1.0.0` during the setup.
- `1.0.0` means the project is declared ready for production use. Only the owner declares it; the skill may ask whether it is time, never decide.
- A version a project template wrote is not a release: a `.csproj` with no `<Version>` (which .NET treats as `1.0.0`) or a fresh `pyproject.toml` saying `0.1.0` does not count. Only a tag or a released changelog section does.

### 5.4 Pre-releases

A pre-release is a version published for testing before the release, written after a hyphen: `0.2.0-rc.1`. `N` counts the attempts within one stage.

| Label | Means | Who tries it | What may still go in |
|---|---|---|---|
| `-alpha.N` | The release's features are still being built; some are missing | The owner or the team | Features and large changes |
| `-beta.N` | Every feature of the release is in; no new feature will be added | People outside the team | Fixes only |
| `-rc.N` | Release candidate: it ships unchanged unless a serious defect turns up | A last trial, close to production | Fixes for serious defects only |

Rules:

- Order: `0.2.0-alpha.1` < `-alpha.2` < `-beta.1` < `-rc.1` < `-rc.2` < `0.2.0`.
- Stages may be skipped. **The default is `rc` alone**; `alpha` and `beta` are used when the owner asks or the project's policy names them.
- A stage never goes back: after `rc.1`, a serious defect gives `rc.2`, not a `beta`, because the new version would sort below one already published.
- `N` starts at 1 in each stage and goes up by one with each new version in it.
- A pre-release tag always points at a commit whose version files declare exactly that pre-release (C6).

### 5.5 The `-dev` marker

On the integration branch, between releases, the version files declare the next version with `-dev`: after `v0.4.0` is tagged, `dev` declares `0.5.0-dev`. Every build is then distinguishable from the release before it, and a version without a label always has a tag. This comes from the prior-art project.

**`-dev` is never tagged or published.** SemVer orders pre-release labels alphabetically, so `0.5.0-dev` sorts above `0.5.0-alpha.1` and `0.5.0-beta.1` although it is older. Keeping `-dev` out of every tag and package keeps published versions in order. (Python's own ordering puts `.dev` before alpha, so the problem does not arise there.)

### 5.6 When to release

The skill suggests a release; it never starts one on its own. It looks at `[Unreleased]` on the integration branch (the production branch in the `main` layout) after a pull request merges there, and when asked:

| `[Unreleased]` on that branch holds | Suggestion |
|---|---|
| A `Security` entry, or a `Fixed` entry for a defect in a released version | A patch release now; a hotfix (§7.5) when the integration branch also holds unreleased features |
| `Added` or `Changed` entries, and the owner says the milestone is finished | A minor (or major) release |
| Nothing, or only internal changes | Nothing |

The suggestion is one line at the end of a reply. If the owner declines, the skill does not repeat it in that session.

## 6. Behavior

### 6.1 First step on every task: is the project set up?

As in `abdullah-docs` §6.1. The project is set up when its release policy (C8) holds an `abdullah-versioning` settings block and `CLAUDE.md` or `AGENTS.md` has the heading `## Versioning (abdullah-versioning)`.

| Found | Then |
|---|---|
| The policy block and the section | Set up: apply the policy. |
| The block, no section | Offer the section only, then continue. Not offered again in the session if declined. |
| Neither | Start the setup (§6.3): survey, show drafts, write nothing until the owner agrees. |

### 6.2 Tasks

| Task | When | What happens |
|---|---|---|
| Status (and the release suggestion) | Asked "what version are we on?", before any release, at the start of the setup | `version.py status`: the layout, the current version from tags, files and changelog, whether they agree, and whether a release is due |
| Plan a release | The owner asks for a release, or accepts a suggestion | `version.py plan`: the proposed version and its reasons; the agent decides `Changed` entries and shows the proposal |
| Release | The owner approves the version | The flow for the project's layout (§7) |
| Pre-release | The owner asks for an alpha, beta or release candidate | The pre-release steps of the layout (§7) |
| Hotfix | A defect in a released version must be fixed before the next release | §7.5; for an older line, §7.5.1 |
| Setup | §6.1 says so, or the owner runs `/setup-abdullah-versioning` | §6.3 |

**What the agent runs and what it asks first.** The script edits files and reads git; it never commits, tags, pushes or calls GitHub. The agent creates branches, commits and local tags, and shows each step. Every step that leaves the machine (push, pull request, merge on GitHub, pushing a tag, a GitHub Release) is shown with its exact command and runs only after the owner approves it.

### 6.3 Setup

The procedure lives in `abdullah-versioning` (`reference/setup.md`); `setup-abdullah-versioning` is a thin user-invoked entry point that calls the Skill tool with `abdullah-versioning` and follows that page, the arrangement of [ADR 0002](../../.agents/adr/0002-setup-owned-by-the-model-invoked-skill.md).

1. **Check Python.** If none of `python`, `python3`, `py -3` runs 3.10 or later, tell the owner the one command that installs it on their system (for example `winget install Python.Python.3.12` on Windows). If they decline, continue by hand and say in every report that the script's checks did not run.
2. **Survey** with `version.py survey`, read-only. It reports:
   - **Tags:** whether any exist, their format (`v1.2.3`, `1.2.3`, `name-1.2.3`), and whether they are SemVer.
   - **Version sources** found (§9.2), with the version each declares.
   - **Changelog:** whether it exists, has `[Unreleased]`, and has released version sections.
   - **Branches:** local and remote, matched to roles (§7.1), and any existing support branches (`support/*`, `maintenance/*`, `release/X.Y.x`); the production branch is the one that holds the release tags, not the repository's default branch, which may be `dev`.
   - **Its verdict:** a new project, or one with releases, and the current version.
3. **Stop and ask** in each of these cases, showing what was found:
   - Tags, files and changelog disagree on the current version.
   - The project has releases but no tags: propose tagging from the next release on; never tag old commits without the owner's word.
   - Tags exist but are not SemVer: ask whether to continue the project's scheme (out of scope, §2) or move to SemVer from the next release.
   - The version lives only in tags (`setuptools-scm`, `hatch-vcs`, MinVer, `git describe`): record the tag as the only source; the script then writes no file.
   - Several unrelated versions (a monorepo): stop, as §2 says.
   - No production branch can be told apart, or the layout is ambiguous.
4. **Choose with the owner:** the layout and branch names (a new project defaults to `dev` → `staging` → `main`), the first version (`0.1.0` unless they choose `1.0.0`), the tag format (`v{version}` for a new project, the existing format otherwise), and whether `alpha` and `beta` are used.
5. **Draft** the release policy with its settings block (§8), and the agent-instructions section (§6.4). Show the drafts.
6. **Write** only after the owner agrees. Creating missing long-lived branches (`dev`, `staging`) is part of the drafts and needs the same approval; pushing them is an outward step (§6.2).
7. **Re-running the setup** on a set-up project shows what changed since the policy was written (new sources, new branches, a changed tag format) and proposes edits; it never overwrites the policy unasked.

### 6.4 The section in the project's agent instructions

Written by the setup with the owner's agreement, under the heading `## Versioning (abdullah-versioning)`:

```
## Versioning (abdullah-versioning)

This project follows the release policy in <policy path>, using the abdullah-versioning skill
(https://github.com/abdoo431/abdullah-skills).
- Never change a declared version, the changelog's version sections or a release tag by hand; use the skill.
- After a pull request merges into <integration branch>, check whether a release is due.
- If your agent cannot load skills, install them from the link above.
```

## 7. Branch layouts and release flows

### 7.1 Roles, not names

The skill works with three branch roles; the policy records each role's name.

| Role | Common names the survey looks for | Layouts |
|---|---|---|
| production | `main`, `master`, `production`, `release`, `trunk`, or any name the owner gives | all |
| staging | `staging`, `stage`, `uat`, `preprod` | `dev-staging-main` |
| integration | `dev`, `develop`, `development` | `dev-staging-main`, `dev-main` |

Work branches follow `type/short-kebab-description`: `feature/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/`, plus `release/X.Y.Z` and `hotfix/X.Y.Z-name`. A project with its own naming keeps it (for example `chore/release-X.Y.Z`); the policy records the release and hotfix branch patterns.

The version files change only on release and hotfix branches, and on the branch that declares the next `-dev` (the prior-art rule).

### 7.2 `dev-staging-main`

```
feature/x ──squash──► dev                                   dev declares 0.2.0-dev
release/0.2.0 from dev: changelog cut, declare 0.2.0-rc.1 ──► staging       tag v0.2.0-rc.1
staging ──► dev (back-merge); declare 0.3.0-dev on dev      dev's [Unreleased] is now only 0.3.0 work
  fix/y from staging ──► staging; declare 0.2.0-rc.2                       tag v0.2.0-rc.2
  staging ──► dev (back-merge)
release/0.2.0-final from staging: declare 0.2.0 ──► staging
staging ──merge commit──► main                              tag v0.2.0 + GitHub Release
main ──► dev (back-merge)
```

- **The cut** (`version.py prepare 0.2.0 --pre rc`) moves `[Unreleased]` into `## [0.2.0] - YYYY-MM-DD` and declares `0.2.0-rc.1`. The release branch merges into `staging`, and the agent tags the merge.
- **Right after the cut, `staging` merges back into `dev`** and `dev` declares `0.3.0-dev` (C16). From then on `dev`'s `[Unreleased]` holds only work for the next version, the release suggestion (§5.6) no longer counts the entries being released, and the later back-merges bring only the fixes.
- **Fixes during staging** go into `staging` through `fix/` branches. Their changelog entries are written under `[Unreleased]`, as `abdullah-docs` always does; the next `declare` on `staging` (the next `rc.N`, or the final) moves them into the `[0.2.0]` section, which is still open because `v0.2.0` has no tag (C17). Each set of fixes the owner wants tried is a new `rc.N`, and `staging` merges back into `dev` after each.
- **The final release** declares `0.2.0` and updates the section's date to the release day, merges `staging` into `main` with a merge commit, and tags the merge commit on `main`. `main` then merges back into `dev`.
- **Without pre-releases** (the owner skips `rc`), the cut declares `0.2.0` directly, `staging` is still where it is tried, and only the final tag is made.
- **`alpha` and `beta`**, when used: `alpha` tags are made on `dev` (on a commit that declares the alpha version, through a `release/` branch), `beta` tags on `staging` before the first `rc`.

### 7.3 `dev-main`

The prior-art flow, with pre-releases added:

```
feature/x ──squash──► dev                                   dev declares 0.2.0-dev
release/0.2.0 from dev: changelog cut, declare 0.2.0 ──squash──► dev
dev ──merge commit──► main   (pull request "release: v0.2.0")   tag v0.2.0 + GitHub Release
release/0.3.0-dev from dev: declare 0.3.0-dev ──squash──► dev
```

- **With pre-releases,** the release branch stays open as the place they are tried: it declares `0.2.0-rc.1` and is tagged there; fixes go into it, their entries under `[Unreleased]` as in §7.2, and the next `declare` gives `rc.2` and moves them into the section; when the owner approves, it declares `0.2.0`, merges into `dev`, and the flow continues as above.
- **The `Fixed`-into-`Added` fold** at the cut: a `Fixed` entry for something first added in this same release folds into its `Added` entry, because the release never had the defect (the prior-art rule).

### 7.4 `main`

The layout of this repository: work merges into the production branch directly.

```
feature/x ──squash──► main                                  main declares the last release, 0.1.0
release/0.2.0 from main: changelog cut, declare 0.2.0 ──► main     tag v0.2.0 + GitHub Release
```

- **No `-dev` marker** by default: between releases the production branch declares the last release, as this repository does today (`.claude-plugin/plugin.json` says `0.1.0`). A project may turn `-dev` on in its policy.
- **Pre-releases** are tagged on the `release/` branch before it merges.

### 7.5 Hotfixes (every layout)

```
hotfix/0.2.1-name from the production branch (in the main layout: from tag v0.2.0)
  failing regression test, the fix, an [Unreleased] entry, prepare 0.2.1
──merge commit──► production branch                         tag v0.2.1 + GitHub Release
back-merge into staging (if any), then into dev (if any); each keeps its own declared version
```

In the `main` layout the production branch may already hold unreleased work, so the hotfix branch starts from the release tag and merges back after tagging.

A hotfix is allowed while a later version is in pre-release: `0.2.1` while `v0.3.0-rc.1` exists, because "the latest release" in the refusals of §9.1 means the latest final tag, never a pre-release tag (C19).

### 7.5.1 Hotfixes for an older release line

The owner decided that a released line older than the latest can get its own fixes (V11): after `0.2.0` has shipped, a user still on `0.1.0` can receive `0.1.1`.

```
support/0.1.x from tag v0.1.0 (created once, the first time line 0.1 needs a fix)
hotfix/0.1.1-name from support/0.1.x
  failing regression test, the fix, an [Unreleased] entry, prepare 0.1.1
──merge commit──► support/0.1.x                             tag v0.1.1 + GitHub Release, not marked latest
forward-port: does the defect exist in newer lines? if yes, fix it there too
```

- **A support branch** is created from the latest final tag of the line, `support/X.Y.x` by default (the policy's `support-branch` pattern), the first time that line needs a fix, with the owner's approval. It is a long-lived branch for that line; the skill never deletes it, and it never declares `-dev`.
- **The version** must stay inside the line and go up: `0.1.1` after `0.1.0`, never `0.2.x`. For a hotfix on a support branch, "the latest release" in the refusals means the latest final tag of that `X.Y` line (C21).
- **The GitHub Release** of an older line is created with `--latest=false`, so the repository's latest release stays the newest version.
- **Forward-porting.** The agent asks whether the defect also exists in newer lines. If it does, the fix goes there too: through a hotfix of the latest line (§7.5), or into the integration branch when the next release is soon enough. The fix is cherry-picked or written again; support branches are never merged into newer branches, so their version files and old code do not travel forward (C22).
- **The changelog on newer branches** also gets the older line's section, so the production branch's changelog lists every release. `version.py carry 0.1.1 --from support/0.1.x` copies the released section into this branch's changelog. Sections are ordered by version, not by date, so `[0.1.1]` sits below `[0.2.0]` (C23).
- **Which lines are supported** is the owner's call each time; the skill does not end a line on its own.

### 7.6 Back-merges

Every back-merge (after a cut, after an `rc.N`, after a final release, after a hotfix) can conflict in three places. The agent resolves them, in this order, and the script makes each step mechanical (C18):

1. **Version files:** take either side, then run `version.py declare <this branch's own version>`, which rewrites every source, lock files included, to the receiving branch's version (`dev` keeps its `-dev`, `staging` its `rc.N`).
2. **The changelog:** keep both sides' entries; released sections come from the side that released them, and `[Unreleased]` keeps the receiving branch's own entries. The result has `[Unreleased]` first and version sections in descending order.
3. **Anything else** is an ordinary merge conflict, resolved as in any merge.

Then `version.py check` must pass before the merge is committed. It reports a source that disagrees with the branch's role, a version section that appears twice, and sections out of order.

### 7.7 Merges, pull requests and tags

- **When the remote is on GitHub and `gh` is available,** every merge into a long-lived branch (`dev`, `staging`, the production branch) goes through a pull request, which respects branch protection. The merge method follows §7.2 to §7.4: squash into the integration branch, a merge commit into `staging` and the production branch. After GitHub merges, the agent fetches and tags the commit GitHub made.
- **On another host, or with no `gh`,** the agent merges locally with the same method, tags locally, and pushes the branch and the tag after the owner approves. The agent may open the host's merge request by hand instead, when the owner prefers.
- **With no remote,** everything stays local; nothing is pushed.
- Every push, pull request, remote merge and GitHub Release is an outward step (§6.2).

## 8. The release policy and its settings

**Where it lives (C8).** A new project gets `docs/RELEASING.md`: the rules of §5 as they apply to this project, the flow of its layout from §7, and the settings block. A project that already documents its releases (for example in `CONTRIBUTING.md`) keeps that document; the setup adds the settings block and fills only what it lacks. The script finds the block with `--policy`, or by looking in `docs/RELEASING.md`, `RELEASING.md`, `CONTRIBUTING.md` and `docs/DOCUMENTATION.md`, in that order.

The block, as the setup would write it for a new .NET project with a web front end:

````
```abdullah-versioning
layout: dev-staging-main
production: main
staging: staging
integration: dev
sources: Directory.Build.props, src/web/package.json, src/web/package-lock.json
tag: v{version}
changelog: CHANGELOG.md
dev-suffix: dev
pre-releases: rc
release-branch: release/{version}
hotfix-branch: hotfix/{version}-{name}
support-branch: support/{major}.{minor}.x
```
````

| Key | Meaning | Default |
|---|---|---|
| `layout` | `dev-staging-main`, `dev-main` or `main` | none: the setup sets it |
| `production`, `staging`, `integration` | The branch name for each role in the layout | `main`, `staging`, `dev` |
| `sources` | Comma-separated version sources (§9.2), or `tag` when the version lives only in tags | none: the setup sets it |
| `tag` | Tag format; `{version}` is the version | `v{version}` |
| `changelog` | The changelog file | `CHANGELOG.md` |
| `dev-suffix` | The label for in-between builds, or `none` | `dev` in layouts with an integration branch, `none` in `main` |
| `pre-releases` | The stages used, from `alpha, beta, rc`, or `none` | `rc` |
| `release-branch`, `hotfix-branch`, `support-branch` | Branch name patterns | `release/{version}`, `hotfix/{version}-{name}`, `support/{major}.{minor}.x` |

Flags on the command line override the block, as in `abdullah-docs` (its C13).

## 9. The script

One script, `version.py`, with subcommands, plus helper modules, in `skills/abdullah-versioning/scripts/`. It shares no files with `abdullah-docs` (skills are separate folders); where it needs the same git helper, it has its own copy.

```
python <skill>/scripts/version.py <command> --root <repo> [--policy <file>] [options]
```

Exit codes: 0 done or clean, 1 refused or problems found, 2 usage error (nothing changed). Findings print one per line as `path:line: severity: kind: message`, the format of `abdullah-docs`. The script never fetches; the agent runs `git fetch` first.

### 9.1 Commands

| Command | Does | Writes |
|---|---|---|
| `survey` | The setup's survey (§6.3 step 2); `--json` for the agent | nothing |
| `status` | Layout, branch roles, current version from tags, sources and changelog, whether they agree, and whether a release looks due | nothing |
| `plan [--pre alpha\|beta\|rc] [--major]` | The proposed next version, each entry that decided it, and the `Changed` entries that need judgment. `--major` is how the agent records its judgment that a `Changed` entry breaks existing use | nothing |
| `prepare X.Y.Z [--pre STAGE] [--date YYYY-MM-DD]` | The cut: move `[Unreleased]` into `## [X.Y.Z] - date`, update the changelog's comparison links, apply the `Fixed`-into-`Added` check (reported, not applied: the agent folds), declare `X.Y.Z` or its first pre-release | changelog, sources |
| `declare VERSION` | Write a version into every source: the next `rc.N`, the final `X.Y.Z` (and the section's date), the next `-dev`, or a branch's own version after a back-merge (§7.6). On a branch with an open version section (no final tag yet), a pre-release or final `declare` also moves the `[Unreleased]` entries into that section (C17) | sources; the changelog for a pre-release or final |
| `notes X.Y.Z` | Print the changelog section, for the GitHub Release | nothing |
| `carry X.Y.Z --from REF` | Copy a released version section from another branch's changelog into this one, in version order (§7.5.1) | changelog |
| `check` | Sources agree with each other; the latest tag, the changelog's latest section and the sources are consistent for the branch's role; no version section appears twice and sections are in order (§7.6) | nothing |

**Refusals,** each before any file changes:

- The version is not valid SemVer, or not greater than the latest release, meaning the latest final tag (and, for a pre-release, than the latest pre-release of the same version). On a support branch, the latest release is the latest final tag of its `X.Y` line, and a version outside that line is refused.
- A pre-release would go back a stage.
- `[Unreleased]` is empty at a cut.
- The sources already disagree.
- The version would be `1.0.0` or higher for the first time without `--first-major`, which the agent passes only after the owner declares 1.0.0.
- The current branch's role does not allow the change (for example a version change on a work branch that is not a release or hotfix branch).

### 9.2 Version sources

Each source type has a small reader and writer that edit only the version text and keep the rest of the file byte for byte.

| Source | Where the version is |
|---|---|
| `Directory.Build.props`, `*.csproj`, `*.fsproj`, `*.vbproj` | `<Version>`; `<VersionPrefix>` with `<VersionSuffix>` when the project uses that pair |
| `pyproject.toml` | `version` under `[project]`, or under `[tool.poetry]` |
| A Python file | `__version__ = "…"` (path named in `sources`) |
| `package.json`, with `package-lock.json` | `"version"`; the lock file at its top level and under `packages[""]` |
| `Cargo.toml`, with `Cargo.lock` | `version` under `[package]`; the package's own entry in the lock file |
| `.claude-plugin/plugin.json` and other JSON manifests | `"version"` at the top level |
| `VERSION` | the whole file |
| `path#regex` | Any other language: one capture group in a pattern the owner approves, for example `src/app.go#const Version = "(.*)"` |
| `tag` | No file; the version is the latest tag |

**Ecosystem forms.** Tags and the changelog always use SemVer (`0.2.0-rc.1`). Each writer uses its ecosystem's form where it differs: Python sources get the PEP 440 form (`0.2.0rc1`, `0.2.0.dev0`), so packaging tools accept and order them; .NET, npm and Cargo take SemVer as it is.

**`AssemblyInfo.cs`** (old-style .NET, four-part `AssemblyVersion`) is reported by the survey but not written; the setup proposes moving the version to `Directory.Build.props`.

## 10. Boundaries with other skills

- **`abdullah-docs`** writes `[Unreleased]` entries during normal work and checks their placement. This skill moves them into version sections. On release, hotfix and staging-fix branches, where entries legitimately land outside `[Unreleased]`, the agent passes `--release` to `check_docs.py`. `abdullah-docs` already hands releases to this skill ([`reference/changelog.md`](../../skills/abdullah-docs/reference/changelog.md)).
- **Changelog fragments.** The `abdullah-docs` design left open whether entries should be fragment files that a release collects (the changesets pattern). **This design keeps the single `CHANGELOG.md`** (C12).
- **Spec-writing skills** are unaffected.

## 11. The repository

Two new folders, laid out like the existing pair:

```
skills/
├── abdullah-versioning/
│   ├── SKILL.md                    model-invoked
│   ├── agents/openai.yaml
│   ├── reference/                  setup.md, rules.md (§5), layouts.md (§7), hotfix.md, sources.md (§9.2)
│   ├── templates/                  releasing.md (the policy), agent-section.md
│   ├── scripts/                    version.py and its helper modules
│   └── tests/                      unittest, with fixture repositories per layout and per source type
└── setup-abdullah-versioning/
    ├── SKILL.md                    disable-model-invocation: true
    └── agents/openai.yaml          policy.allow_implicit_invocation: false
```

Also, in the same change: both skills in `README.md` and in the `skills` array of `.claude-plugin/plugin.json`; a page each in `docs/` from `.agents/writing-docs.md` and a row each in `docs/README.md`; the skill table and layout in `CLAUDE.md` and `AGENTS.md`; an `Added` entry in `CHANGELOG.md`; the test command for the new skill in the "Checks" section and in `.github/workflows/check.yml`.

**This repository uses the skill on itself** from its next release: layout `main`, source `.claude-plugin/plugin.json`, tag `v{version}`, no `-dev`. The "Releases" section of `CLAUDE.md` and `AGENTS.md` then points to the skill and its policy.

## 12. How it is verified

- **Script tests** on fixture repositories: each layout; each source type, including a file whose formatting must survive byte for byte; a new project; a project with releases but no tags; disagreeing sources; non-SemVer tags; a version only in tags; each refusal in §9.1; a hotfix on a support branch, a version outside its line refused, and `carry` placing an older line's section by version; pre-release ordering, including a refused step back from `rc` to `beta`; the PEP 440 forms; the `-dev` marker never reaching a tag.
- **On a real project with releases:** `survey` and `status`, read-only, on the owner's earlier private project (`dev-main`, three source files, seven tags) report its layout, its sources and `0.7.0` correctly; `plan` on its current `[Unreleased]` gives a proposal the owner agrees with. Every finding is shown to the owner.
- **On a new project:** the setup on a small sample project shows its drafts before writing, and a first release goes from `0.1.0-dev` through `0.1.0-rc.1` to `v0.1.0` on the `dev-staging-main` layout.
- **On this repository:** its next release is cut with the skill.

## 13. Decisions

The owner's decisions:

| # | Decision |
|---|---|
| V1 | The skill works on projects in any language: .NET, Python and others. |
| V2 | The skill owns the numbering: the next version, which part goes up, and where the version is stored. |
| V3 | The skill tells the owner when a release is due. |
| V4 | It works on projects that already have releases and on new ones, and tells them apart: releases or not, where the version is declared, tags or not. |
| V5 | Clear rules for `0.1.0`, `1.0.0`, and when each part changes (§5). |
| V6 | The release flow, branches and merges follow the owner's earlier private project, generalized. |
| V7 | Pre-release labels `-alpha.N`, `-beta.N`, `-rc.N` are explained and supported. |
| V8 | Three layouts: `dev` → `staging` → `main`, `dev` and `main`, and `main` alone. A new project defaults to `dev` → `staging` → `main`. The production branch may be called `master` or anything else. |
| V9 | Approach A: one skill plus a standard-library script (§4). |
| V10 | The script is Python, not JavaScript. |
| V11 | An older release line can get its own hotfixes (`0.1.1` after `0.2.0` has shipped). |

Calls made by the designer, open to correction:

| # | Call | Reason |
|---|---|---|
| C1 | SemVer 2.0.0 is the only scheme in version 1. | It carries the breaking-change signal V5 asks for, and every ecosystem in V1 accepts it. |
| C2 | The part that goes up is derived from `[Unreleased]` entries, not from commit messages. | `abdullah-docs` keeps those entries in every project, written for users; commit conventions vary between projects. |
| C3 | Before 1.0.0, any feature-level entry gives MINOR and fixes alone give PATCH; breaking changes give MINOR. | SemVer's `0.y.z` rule, and the prior-art "a minor is a milestone". |
| C4 | The proposed version and its reasons are shown before anything is written. | Anti-goal: nothing written without approval. |
| C5 | The release suggestion is one line, after merges into the integration branch, and not repeated in a session once declined. | Useful without nagging. |
| C6 | A pre-release tag points at a commit that declares that exact pre-release. | A build from the tag reports the tagged version; traceability from version to commit. |
| C7 | `-dev` is never tagged or published; it is off by default in the `main` layout. | SemVer would sort it above `alpha` and `beta` (§5.5); in this repository a changed plugin version would also update every install. |
| C8 | The policy lives in `docs/RELEASING.md` for a new project, or in the project's existing release document. | A release process is an operational procedure that deserves its own page; existing projects keep their documents (`abdullah-docs` C1, C8). |
| C9 | The setup procedure lives in `abdullah-versioning`; `setup-abdullah-versioning` is a thin entry point. | ADR 0002's reason applies unchanged. |
| C10 | The script never commits, tags, pushes or calls GitHub; the agent does, and asks before every outward step. | Deterministic edits in the script, judgment and approval with the agent. |
| C11 | Monorepos with independent versions and non-SemVer schemes are detected and declined in version 1. | Each is a design of its own. |
| C12 | One `CHANGELOG.md`, no fragment files. | `check_docs.py` already catches a misplaced entry, the problem fragments would solve; fragments would change how `abdullah-docs` writes entries in every project. |
| C13 | Python sources get PEP 440 forms; tags and the changelog stay SemVer. | Packaging tools order PEP 440; one form for tags keeps them comparable across projects. |
| C14 | A release ends with the tag and, when the remote is GitHub and `gh` is available, a GitHub Release from `notes`. | The prior-art project's last step; publishing packages is the project's own (§2). |
| C15 | The production branch is the one holding the release tags, not the repository's default branch. | The prior-art project's default branch was `dev`. |
| C16 | In `dev-staging-main`, `staging` merges back into `dev` right after the cut, and `dev` declares the next `-dev` then. | Otherwise `dev`'s `[Unreleased]` keeps the entries being released, the release suggestion counts them again, and the final back-merge duplicates them. |
| C17 | Entries are always written under `[Unreleased]`, even on `staging` and open release branches; the next pre-release or final `declare` moves them into the open version section. | `abdullah-docs` keeps one rule everywhere and needs no change. |
| C18 | The agent resolves back-merge conflicts, with `declare` and `check` making the version and changelog steps mechanical (§7.6). | No separate merge command to build; the two commands already exist. |
| C19 | "The latest release" in the refusals means the latest final tag; pre-release tags of a later version do not block a hotfix. | A hotfix on the released line is normal while the next version is in `rc`. |
| C20 | Merges into long-lived branches go through pull requests on GitHub with `gh`, and are local merges pushed after approval elsewhere (§7.7). | Branch protection on GitHub; a working flow on any other host or none. |
| C21 | An older line is kept on a `support/X.Y.x` branch created from its latest tag when it first needs a fix; versions on it stay inside `X.Y`. | One place per line to fix and tag; the refusals stay simple. |
| C22 | Fixes travel forward by cherry-pick or rewrite, never by merging a support branch into a newer one. | A merge would carry the old line's version files and code forward. |
| C23 | The production branch's changelog lists older-line releases too, ordered by version, copied with `carry`. | One changelog answers "which versions exist"; version order matches SemVer and the order check. |

## 14. Left to the builder

- The helper modules' split, and how much of `abdullah-docs`' git and finding helpers to copy.
- The exact `survey --json` shape, as long as the agent can read every finding in §6.3 from it.
- The exact wording of `SKILL.md` and the reference pages, within the rules of `CLAUDE.md`.
- Fixture construction for the tests.
