# Changelog

All notable changes to this project are recorded in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

## [0.2.0] - 2026-11-26

### Added

- `abdullah-versioning` skill: proposes the next version and which part goes up from the changelog's `[Unreleased]` entries, keeps every file that declares the version in agreement (.NET, Python, Node, Rust, plugin manifests, a `VERSION` file, or any file through a pattern), and runs releases, pre-releases, hotfixes and fixes for older release lines on a `dev` → `staging` → `main`, `dev` and `main`, or `main` layout. See [docs/abdullah-versioning.md](docs/abdullah-versioning.md).
- `setup-abdullah-versioning` skill: surveys a project's tags, version files, changelog and branches, tells a new project from one with releases, and drafts its release policy and agent-instructions section for approval before writing them. See [docs/setup-abdullah-versioning.md](docs/setup-abdullah-versioning.md).

### Changed

- `abdullah-docs`: `--release` also applies on branches that fix a release candidate on `staging`.
- Install routes: Claude Code, Codex and `npx skills` are marked tested against the published repository, with the agent versions used; Copilot and Gemini stay untested. The `npx skills` route shows the command that installs without prompts.

## [0.1.0] - 2026-11-25

### Added

- `abdullah-docs` skill: keeps a project's ADRs, changelog, specs, runbooks, incident records and READMEs traceable under the project's own documentation policy, with scripts that number and index ADRs, check links, code paths, ADR numbers and changelog placement against the main branch, and list the definition-of-done items. See [docs/abdullah-docs.md](docs/abdullah-docs.md).
- `setup-abdullah-docs` skill: surveys a project, asks for the `lean` or `full` profile, and drafts its documentation policy, map, templates and agent-instructions section for approval before writing them. See [docs/setup-abdullah-docs.md](docs/setup-abdullah-docs.md).
