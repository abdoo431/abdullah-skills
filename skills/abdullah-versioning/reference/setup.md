# Setup

Set a project up for releases: survey it, agree the choices with the owner, and write its release policy and the section in its agent instructions. Write nothing until the owner has seen the drafts and agreed.

## 1. Check Python

Try `python`, `python3`, then `py -3`; the script needs 3.10 or later. If none runs, tell the owner the one command that installs it on their system (for example `winget install Python.Python.3.12` on Windows, `brew install python` on macOS, the distribution's package on Linux). If they decline, continue by hand and say in every report that the script's checks did not run.

## 2. Survey

Run `git fetch`, then `version.py survey --root <repo>` (add `--json` to read it field by field). It reports, read-only:

- **Tags:** the version tags, their format (`v{version}`, `{version}`, `<prefix>{version}`), and other tags it ignored.
- **Sources:** every place a version is declared, with its value ([sources.md](sources.md)).
- **Changelog:** whether it exists, has `[Unreleased]`, and its released sections.
- **Branches:** each role's branch, support branches, and the layout they suggest. The production branch is the one holding the release tags, not the repository's default branch, which may be `dev`.
- **Verdict:** `new` (no tags, no released sections), `released` (with the current version), or `ambiguous`.
- **Stops:** every reason to ask the owner before going on.

## 3. Stop and ask

For each `stop:` line, show the owner what was found and ask:

| Stop | Ask |
|---|---|
| Tags, files and changelog disagree | Which is right; then make the others agree through `version.py declare` on a branch |
| Released versions but no tags | Whether to tag from the next release on. Never tag old commits without the owner's word |
| Version tags that are not SemVer (`2024.05`) | Whether to move to SemVer from the next release. Continuing another scheme is not supported |
| The version lives only in tags | Confirm; the source is then `tag` and no file is written |
| Several unrelated versions (a monorepo) | Stop: independently versioned packages are not supported |
| No production branch, or an ambiguous layout | Which branch is production, and which layout the project follows |

Also report any `AssemblyInfo.cs` the survey found ([sources.md](sources.md#choosing-sources-during-the-setup)).

## 4. Choose with the owner

Propose each, with the survey's finding, and let the owner change it:

- **Layout and branch names.** An existing project keeps its layout and names. A new project defaults to `dev-staging-main`: `dev` → `staging` → `main` ([layouts.md](layouts.md)). The production branch may be called `master` or anything else.
- **Sources.** The ones the survey found, confirmed one by one.
- **First version.** For a new project, `0.1.0` unless the owner chooses `1.0.0` (`first-version` in the policy).
- **Tag format.** `v{version}` for a new project; the existing format otherwise.
- **Pre-releases.** `rc` by default; `alpha` and `beta` only if the owner wants them.
- **`-dev`.** On for layouts with an integration branch, off for `main`.

## 5. Draft

- **The release policy.** A new project gets `docs/RELEASING.md`, filled in from [../templates/releasing.md](../templates/releasing.md) with the choices of step 4 and only the layout it uses. A project that already documents its releases (for example in `CONTRIBUTING.md`) keeps that document: add the settings block there and fill in only what it lacks.
- **The agent section.** From [../templates/agent-section.md](../templates/agent-section.md), with `{policy}` and `{integration}` filled in (the production branch in the `main` layout), for `CLAUDE.md` and `AGENTS.md` (whichever exist; both when both do).
- **Branches.** A new project in `dev-staging-main` or `dev-main` needs `dev` (and `staging`) created from the production branch.

Show every draft to the owner.

## 6. Write

Only after the owner agrees: write the policy, add the agent section under its heading `## Versioning (abdullah-versioning)` (when the file already says some of it, add only the missing lines under the heading), and create the branches. Pushing new branches is an outward step: show the command and wait for approval.

If the project uses `abdullah-docs`, add the policy to its documentation map (`docs/README.md`).

## 7. Confirm

Run `version.py status` and `version.py check` on the current branch. Both must agree with what the owner chose. Report the setup in a few lines: the layout, the sources, the current version, and any stop that is still open.

## Re-running the setup

On a project that is already set up, run the survey again and compare it with the policy's settings block: new or removed sources, new branches, a changed tag format, a support branch. Show each difference and propose the edit; never overwrite the policy unasked.
