# Releasing

This document says how this repository numbers its versions and cuts releases. It is the repository's rule; the [abdullah-versioning](../skills/abdullah-versioning/SKILL.md) skill applies it.

```abdullah-versioning
layout: main
production: main
sources: .claude-plugin/plugin.json
tag: v{version}
changelog: CHANGELOG.md
dev-suffix: none
pre-releases: rc
first-version: 0.1.0
release-branch: release/{version}
hotfix-branch: hotfix/{version}-{name}
support-branch: support/{major}.{minor}.x
```

The block above holds the settings the release script reads. A key left out means the default.

## Versions

This repository follows [Semantic Versioning 2.0.0](https://semver.org/spec/v2.0.0.html): `MAJOR.MINOR.PATCH`.

- **Before 1.0.0:** MINOR goes up when a milestone is released; PATCH for fixes to a released version. A breaking change raises MINOR.
- **1.0.0** is the first release declared ready for production use, by the owner.
- **From 1.0.0:** MAJOR for a change that breaks existing use, MINOR for a backward-compatible feature, PATCH for fixes.
- **Pre-releases** are `X.Y.Z-rc.N`, tagged for testing before the release.
- **Between releases** `main` declares the last release; there is no `-dev` version, because every change of `version` in `.claude-plugin/plugin.json` updates every plugin install.

The version is declared once, in `.claude-plugin/plugin.json`. Only release and hotfix branches change it, through the skill.

## Branches

- Finished work lands on `main` through pull requests, squash-merged.
- A release: `release/X.Y.Z` from `main` cuts the changelog and declares `X.Y.Z`, merges into `main`, and the release commit is tagged `vX.Y.Z`, with a GitHub Release made from its changelog section.

## Hotfixes

- A fix to the latest release: `hotfix/X.Y.Z-name` from the release tag, with a regression test and a changelog entry, merged into `main` and tagged.
- A fix to an older line: a support branch for that line, named by the `support-branch` pattern above, from the line's latest tag, created once; hotfixes for the line branch from it and are tagged there; the fix is carried forward by cherry-pick, never by merging the support branch.

## Changelog

`CHANGELOG.md` follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/). Entries are written under `[Unreleased]`; a release moves them into its version section, and a repository test checks that the newest section matches `version` in `.claude-plugin/plugin.json`. Released sections are never edited.
