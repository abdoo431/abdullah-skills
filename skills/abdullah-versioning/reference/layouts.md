# Branch layouts and release flows

The policy's `layout` names one of three flows. Branch names come from the policy (`production`, `staging`, `integration`, and the `release-branch`, `hotfix-branch` and `support-branch` patterns); the names below are the defaults.

Before every flow: `git fetch`, `version.py status` and `version.py plan`, and the owner's approval of the version ([../SKILL.md](../SKILL.md#planning-a-release)). Commit messages follow the project's conventions.

## Roles, not names

| Role | Common names | Layouts |
|---|---|---|
| production | `main`, `master`, `production`, `release`, `trunk` | all |
| staging | `staging`, `stage`, `uat`, `preprod` | `dev-staging-main` |
| integration | `dev`, `develop`, `development` | `dev-staging-main`, `dev-main` |

Work branches are `type/short-kebab-description` (`feature/`, `fix/`, `docs/`, `refactor/`, `test/`, `chore/`), plus `release/X.Y.Z` and `hotfix/X.Y.Z-name`, unless the project names them its own way. Version files change only on release and hotfix branches and on the branch that declares the next `-dev`.

## `dev-staging-main`

```
feature/x ──squash──► dev                                   dev declares 0.2.0-dev
release/0.2.0 from dev: changelog cut, declare 0.2.0-rc.1 ──► staging       tag v0.2.0-rc.1
staging ──► dev (back-merge); declare 0.3.0-dev on dev
  fix/y from staging ──► staging; declare 0.2.0-rc.2                       tag v0.2.0-rc.2
  staging ──► dev (back-merge)
release/0.2.0-final from staging: declare 0.2.0 ──► staging
staging ──merge commit──► main                              tag v0.2.0 + GitHub Release
main ──► dev (back-merge)
```

1. **Cut.** `release/0.2.0` from `dev`: `version.py prepare 0.2.0 --pre rc`, apply the fold ([rules.md](rules.md#the-fixed-into-added-fold)), commit. Merge into `staging` with a merge commit; tag the merge `v0.2.0-rc.1`.
2. **Right after the cut, back-merge `staging` into `dev`** ([Back-merges](#back-merges)), and declare the next `-dev` on `dev` (`version.py declare 0.3.0-dev`). From then on `dev`'s `[Unreleased]` holds only the next version's work.
3. **Fixes on staging.** Each fix is a `fix/` branch from `staging`, its entry under `[Unreleased]`, merged into `staging`. When the owner wants the fixes tried: a branch from `staging`, `version.py declare 0.2.0-rc.2` (it moves the new entries into `[0.2.0]`), merge, tag `v0.2.0-rc.2`, then back-merge `staging` into `dev`.
4. **Final.** A branch from `staging`: `version.py declare 0.2.0 --date <release day>`, merge into `staging`, then `staging` into `main` with a merge commit. Tag the merge commit on `main` `v0.2.0`, and create the GitHub Release ([Merges, pull requests and tags](#merges-pull-requests-and-tags)). Back-merge `main` into `dev`.
5. **Without pre-releases,** step 1 runs `version.py prepare 0.2.0` and only the final tag is made; `staging` is still where it is tried.
6. **`alpha` and `beta`,** when used: alpha tags on `dev` (a `release/` branch declares the alpha, merged into `dev`, then tagged), beta tags on `staging` before the first `rc`.

## `dev-main`

```
feature/x ──squash──► dev                                   dev declares 0.2.0-dev
release/0.2.0 from dev: changelog cut, declare 0.2.0 ──squash──► dev
dev ──merge commit──► main   (pull request "release: v0.2.0")   tag v0.2.0 + GitHub Release
release/0.3.0-dev from dev: declare 0.3.0-dev ──squash──► dev
```

1. **Cut.** `release/0.2.0` from `dev`: `version.py prepare 0.2.0`, the fold, commit, squash into `dev`.
2. **Release.** A pull request from `dev` into `main` titled `release: v0.2.0`, merged with a merge commit (never squashed). Tag the merge commit on `main`; create the GitHub Release.
3. **Next.** `release/0.3.0-dev` from `dev`: `version.py declare 0.3.0-dev`, squash into `dev`.
4. **With pre-releases,** the release branch stays open: `prepare 0.2.0 --pre rc`, tag `v0.2.0-rc.1` on it; fixes go into it with entries under `[Unreleased]`; `declare 0.2.0-rc.2` and tag; when the owner approves, `declare 0.2.0`, squash into `dev`, and continue with step 2.

## `main`

```
feature/x ──squash──► main                                  main declares the last release
release/0.2.0 from main: changelog cut, declare 0.2.0 ──► main     tag v0.2.0 + GitHub Release
```

No `-dev` by default: between releases the production branch declares the last release. Pre-releases are tagged on the `release/` branch before it merges.

## Back-merges

Every back-merge (after a cut, an `rc.N`, a final release, a hotfix) can conflict in version files and the changelog, and even a merge without conflicts can put the receiving branch's new entries inside a version section. Back-merge only after a `declare` has moved the sending branch's entries into its version section. Then, conflict or not:

1. **Version files:** on a conflict, take the receiving branch's side (`git checkout --ours <file>` while merging into it). Always run `version.py declare <the receiving branch's own version>`.
2. **The changelog:** on a conflict, take the receiving branch's side. Then, for every version section the sending branch has, run `version.py carry X.Y.Z --from <sending branch> --replace` when this branch has the section, and `version.py carry X.Y.Z --from <sending branch>` when it lacks it. `--replace` makes the section the sending branch's copy and moves any entry only this branch had back under `[Unreleased]`.
3. **Anything else:** resolve as in any merge.
4. `version.py check` must pass before the merge is committed.

Do this either on the receiving long-lived branch itself in a local merge (pass `--allow-long-lived` to `declare`), or on a branch named with the release pattern, for example `release/0.3.0-dev-merge`, that then merges into it. A work branch (`chore/…`) may not change the version.

## Merges, pull requests and tags

- **On GitHub with `gh`:** every merge into a long-lived branch goes through a pull request: squash into the integration branch, a merge commit into `staging` and the production branch. After GitHub merges, `git fetch`, then tag the commit GitHub made: `git tag -a vX.Y.Z -m vX.Y.Z <commit>`. Push the tag, then `version.py notes X.Y.Z > <scratch file>` and `gh release create vX.Y.Z --title vX.Y.Z --notes-file <scratch file>` (add `--prerelease` for a pre-release).
- **On another host, or without `gh`:** merge locally with the same method, tag locally, and push the branch and the tag; or open the host's merge request by hand when the owner prefers.
- **With no remote:** everything stays local; nothing is pushed.
- Every push, pull request, remote merge and release is an outward step: show its command and wait for the owner's approval.
