# Releasing

This document says how this project numbers its versions and cuts releases. It is the project's rule; the [abdullah-versioning](https://github.com/abdoo431/abdullah-skills) skill applies it.

```abdullah-versioning
layout: dev-staging-main
production: main
staging: staging
integration: dev
sources: VERSION
tag: v{version}
changelog: CHANGELOG.md
dev-suffix: dev
pre-releases: rc
first-version: 0.1.0
release-branch: release/{version}
hotfix-branch: hotfix/{version}-{name}
support-branch: support/{major}.{minor}.x
```

The block above holds the settings the release script reads. A key left out means the default.

## Versions

This project follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html): `MAJOR.MINOR.PATCH`.

- **Before 1.0.0:** MINOR goes up when a milestone is released; PATCH for fixes to a released version. A breaking change raises MINOR.
- **1.0.0** is the first release declared ready for production use, by the owner.
- **From 1.0.0:** MAJOR for a change that breaks existing use, MINOR for a backward-compatible feature, PATCH for fixes.
- **Pre-releases** are `X.Y.Z-rc.N` (and `-alpha.N`, `-beta.N` when used), tagged for testing before the release.
- **Between releases** the integration branch declares the next version with `-dev`. It is never tagged or published.

The version is declared in the files listed under `sources` above, which always agree. Only release and hotfix branches change them, through the skill.

## Branches

<!-- Keep the section of the layout this project uses, and delete the other two. -->

### dev → staging → main

- `main` holds released versions only; every commit on it is tagged.
- `staging` is where a release candidate is tried before it ships.
- `dev` is where finished work lands, through pull requests from work branches (`feature/`, `fix/`, `docs/`, `chore/`), squash-merged.
- A release: `release/X.Y.Z` from `dev` cuts the changelog and declares `X.Y.Z-rc.1`, and merges into `staging`; fixes on `staging` give `rc.2` and later; the final release declares `X.Y.Z`, `staging` merges into `main` with a merge commit, and the merge commit is tagged `vX.Y.Z`.
- After each step, `staging` (or `main`) merges back into `dev`, which declares the next `-dev`.

### dev → main

- `main` holds released versions only; every commit on it is tagged.
- `dev` is where finished work lands, through pull requests from work branches, squash-merged.
- A release: `release/X.Y.Z` from `dev` cuts the changelog and declares `X.Y.Z`, squash-merged into `dev`; a pull request `release: vX.Y.Z` merges `dev` into `main` with a merge commit, which is tagged `vX.Y.Z`; then `dev` declares the next `-dev`.

### main

- Finished work lands on `main` through pull requests, squash-merged.
- A release: `release/X.Y.Z` from `main` cuts the changelog and declares `X.Y.Z`, merges into `main`, and is tagged `vX.Y.Z`.

## Hotfixes

- A fix to the latest release: `hotfix/X.Y.Z-name` from `main` (from the release tag in the `main` layout), with a regression test and a changelog entry, merged into `main` with a merge commit and tagged; then merged back into each branch above it.
- A fix to an older line: `support/X.Y.x` from that line's latest tag, created once; hotfixes for the line branch from it and are tagged there; the fix is carried forward to newer lines by cherry-pick, never by merging the support branch.

## Changelog

`CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Entries are written under `[Unreleased]`; a release moves them into its version section. Released sections are never edited.
