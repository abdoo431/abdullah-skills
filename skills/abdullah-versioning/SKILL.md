---
name: abdullah-versioning
description: "Own a project's version number and releases in any language: propose the next version and which part goes up from the changelog, keep every declared version in agreement, cut releases, pre-releases and hotfixes on the project's branch layout, and say when a release is due. Use when a release, version, tag, pre-release or hotfix is asked for, after a pull request merges into the integration branch, and before changing a version file or the changelog's version sections."
---

# abdullah-versioning

This skill answers the question `abdullah-docs` leaves to it: **when did this ship, and in which version?** It decides the next version from the changelog, finds every place the project declares its version, and runs the release on the project's own branches. Paths below are relative to this skill's folder (the folder that holds this file).

## Rules that always apply

- The project's written release policy wins over this skill's defaults. You may propose a change to a project rule; never apply it on your own.
- **Show before writing.** Show the proposed version and its reasons before any file changes; the owner approves or changes it.
- **Ask before every outward step.** Pushing, opening or merging a pull request, pushing a tag, and creating a GitHub Release each run only after the owner approves that step, shown with its exact command. Local branches, commits and tags need no separate approval once the owner approved the release.
- **Never declare `1.0.0` on your own.** Only the owner declares it; you may ask whether it is time.
- **Never guess.** When tags, version files and the changelog disagree, stop and show what you found.
- **Never rewrite history.** Do not edit a released changelog section, and never move or delete an existing tag.
- **Never change a version by hand.** Use `version.py`, which writes every source at once and refuses a bad state.
- **`-dev` is never tagged or published.**
- Keep the project's existing branch names, tag format and habits.

## Step 0: is the project set up?

Do this first on every task. The project is set up when both are true:

1. A release policy holds an `abdullah-versioning` settings block: `docs/RELEASING.md`, `RELEASING.md`, `CONTRIBUTING.md` or `docs/DOCUMENTATION.md`.
2. `CLAUDE.md` or `AGENTS.md` has the heading `## Versioning (abdullah-versioning)`.

| Found | Then |
|---|---|
| The block and the section | Set up. Apply the policy. |
| The block, no section | Offer the section only (step 6 of [reference/setup.md](reference/setup.md)), then continue. Not offered again in the session if declined. |
| Neither | Tell the owner the project has no release policy, that you will survey it and show drafts before writing anything, and follow [reference/setup.md](reference/setup.md). If the owner declines, do not release: say what the setup would need, and do not offer it again in this session. The owner can run it later with `/setup-abdullah-versioning` (listed as `/abdullah-skills:setup-abdullah-versioning` when installed as a plugin). |

## Tasks

| Task | When | What to do |
|---|---|---|
| Status | "What version are we on?", before any release | `version.py status` |
| Plan a release | The owner asks for a release, or accepts a suggestion | `version.py plan`, then [Planning a release](#planning-a-release) |
| Release | The owner approved the version | The flow for the policy's layout: [reference/layouts.md](reference/layouts.md) |
| Pre-release | An alpha, beta or release candidate is asked for | [reference/rules.md](reference/rules.md#pre-releases) and the layout's pre-release steps |
| Hotfix | A released version needs a fix before the next release | [reference/hotfix.md](reference/hotfix.md) |
| Fix for an older line | A user on an older release line needs a fix | [reference/hotfix.md](reference/hotfix.md#an-older-release-line) |
| Back-merge | A release branch, `staging` or the production branch merges back into a branch above it | [reference/layouts.md](reference/layouts.md#back-merges) |
| Setup | Step 0 says so, or the owner asks | [reference/setup.md](reference/setup.md) |

The numbering rules (which part goes up, `0.1.0`, `1.0.0`, pre-releases, `-dev`) are in [reference/rules.md](reference/rules.md). Where each language declares its version is in [reference/sources.md](reference/sources.md).

## Running the script

The script is in this skill's `scripts/` folder. Run it with Python 3.10 or later:

```
python <this skill's folder>/scripts/version.py <command> --root <repo> [--policy <policy file>]
```

| Command | Does | Writes |
|---|---|---|
| `version.py survey [--json]` | The setup's survey: tags, sources, changelog, branches, the verdict, and every reason to stop | nothing |
| `version.py status [--json]` | Layout, branch role, latest release, declared versions, whether they agree, whether a release is due | nothing |
| `version.py plan [--pre STAGE] [--major] [--json]` | The proposed next version, the entries that decide it, and the `Changed` entries you must judge | nothing |
| `version.py notes X.Y.Z` | Prints a changelog section, for the GitHub Release | nothing |
| `version.py check` | Declared versions agree, suit the branch's role, and the changelog's sections are in order | nothing |
| `version.py prepare X.Y.Z [--pre STAGE] [--date D]` | The cut: moves `[Unreleased]` into `[X.Y.Z]` and declares `X.Y.Z` or its first pre-release | changelog, sources |
| `version.py declare VERSION [--date D]` | Declares the next `rc.N`, the final release, the next `-dev`, or a branch's own version after a back-merge | sources; the changelog for a pre-release or final |
| `version.py carry X.Y.Z --from REF` | Copies a released section from another branch's changelog, in version order | changelog |

- `--first-major` is passed only after the owner declares `1.0.0`. `--allow-long-lived` is passed only in a local merge on the production, staging or integration branch itself (no pull request).
- Exit codes: 0 done or clean, 1 refused or errors found, 2 usage error. A refusal changes no file; read its message, fix the cause, and run it again. Never work around a refusal by editing files by hand.
- Findings are one per line: `path:line: severity: kind: message`.
- The script never fetches, commits, tags, pushes or calls GitHub. Run `git fetch` first, so tags and branches are current.
- If Python is not available (try `python`, `python3`, then `py -3`), tell the owner the one command that installs it (for example `winget install Python.Python.3.12` on Windows). If they decline, do the steps by hand from the reference pages, and say in every report that the script's checks did not run.

## Planning a release

1. Run `git fetch`, then `version.py status`. If `agree` is `no` or a finding is an error, stop and show it.
2. Run `version.py plan` (add `--pre rc` for a release candidate).
3. Read every `judge:` line. A `Changed` entry that breaks existing use (a public API, a data format, a command, an event name) makes the release a major one from `1.0.0` on: run `plan --major`. When unsure, ask the owner.
4. Show the owner the proposal in one line, with its reasons, for example: "`0.3.0` → `0.4.0`, because `Added`: workspace export." Before `1.0.0`, a release is a finished milestone; ask whether the milestone is done if that is not clear.
5. After the owner approves, follow the layout's flow in [reference/layouts.md](reference/layouts.md).

## When a release is due

After a pull request merges into the integration branch (the production branch in the `main` layout), and when asked, run `version.py status` and read `due`:

| `due` | Say |
|---|---|
| `patch: Security` or `patch: Fixed` | A patch release is due now; a hotfix ([reference/hotfix.md](reference/hotfix.md)) when the integration branch also holds unreleased features |
| `minor when the milestone is finished: …` | A release is due when the owner says the milestone is finished |
| `none` | Nothing |

Say it in one line at the end of your reply. If the owner declines, do not repeat it in this session.

## Working with abdullah-docs

`abdullah-docs` writes the `[Unreleased]` entries this skill releases. Entries are always written under `[Unreleased]`, even on `staging` and on open release branches; `declare` moves them into the open version section. On release, hotfix and staging-fix branches, pass `--release` to its `check_docs.py`. When it is installed, call the Skill tool with `abdullah-docs` (listed as `abdullah-skills:abdullah-docs` when installed as a plugin) for its done check before a release pull request.
