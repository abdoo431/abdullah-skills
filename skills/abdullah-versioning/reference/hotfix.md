# Hotfixes

A hotfix fixes a released version before the next release. Branch patterns come from the policy (`hotfix-branch`, `support-branch`).

## The latest release

```
hotfix/0.2.1-name from the production branch (in the main layout: from tag v0.2.0)
  failing regression test, the fix, an [Unreleased] entry, prepare 0.2.1
──merge commit──► production branch                         tag v0.2.1 + GitHub Release
back-merge into staging (if any), then into dev (if any); each keeps its own declared version
```

1. Branch from the production branch. In the `main` layout the production branch may hold unreleased work: branch from the release tag instead (`git checkout -b hotfix/0.2.1-name v0.2.0`).
2. Write a regression test that fails, then the fix, then the entry under `[Unreleased]` (`Fixed` or `Security`).
3. `version.py prepare 0.2.1`, commit.
4. Merge into the production branch with a merge commit; tag the merge `v0.2.1`; create the GitHub Release.
5. Back-merge the production branch into `staging` (if the layout has it), then into `dev` (if it has it), as in [layouts.md](layouts.md#back-merges). Each keeps its own declared version.

A hotfix is allowed while a later version is in pre-release: `0.2.1` while `v0.3.0-rc.1` exists. "The latest release" means the latest final tag, never a pre-release tag.

## An older release line

After `0.2.0` has shipped, a user still on `0.1.0` can receive `0.1.1`.

```
support/0.1.x from tag v0.1.0 (created once, the first time line 0.1 needs a fix)
hotfix/0.1.1-name from support/0.1.x
  failing regression test, the fix, an [Unreleased] entry, prepare 0.1.1
──merge commit──► support/0.1.x                             tag v0.1.1 + GitHub Release, not marked latest
forward-port: does the defect exist in newer lines? if yes, fix it there too
```

1. **The support branch.** The first time a line needs a fix, propose `support/0.1.x` from the line's latest final tag, and create it after the owner approves. It is long-lived: never delete it, and it never declares `-dev`. Which lines are supported is the owner's call each time.
2. **The hotfix.** `hotfix/0.1.1-name` from the support branch, the test, the fix, the entry, `version.py prepare 0.1.1`. The script compares with the latest tag of the `0.1` line and refuses a version outside it.
3. **Release.** Merge into the support branch with a merge commit; tag `v0.1.1`; create the GitHub Release with `--latest=false`, so the repository's latest release stays the newest version.
4. **Forward-port.** Ask whether the defect also exists in newer lines. If it does, fix it there too: a hotfix of the latest line, or a fix into the integration branch when the next release is soon. Cherry-pick or rewrite the fix; never merge a support branch into a newer branch, because its version files and old code would travel with it.
5. **The changelog on newer branches.** On the production branch (through a branch and pull request where the project uses them), run `version.py carry 0.1.1 --from support/0.1.x`. Sections are ordered by version, so `[0.1.1]` sits below `[0.2.0]`.
