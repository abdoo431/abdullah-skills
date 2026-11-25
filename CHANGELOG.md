# Changelog

All notable changes to this project are recorded in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [Unreleased]

### Changed

- Install routes: Claude Code, Codex and `npx skills` are marked tested against the published repository, with the agent versions used; Copilot and Gemini stay untested. The `npx skills` route shows the command that installs without prompts.

## [0.1.0] - 2026-11-25

### Added

- `abdullah-docs` skill: keeps a project's ADRs, changelog, specs, runbooks, incident records and READMEs traceable under the project's own documentation policy, with scripts that number and index ADRs, check links, code paths, ADR numbers and changelog placement against the main branch, and list the definition-of-done items. See [docs/abdullah-docs.md](docs/abdullah-docs.md).
- `setup-abdullah-docs` skill: surveys a project, asks for the `lean` or `full` profile, and drafts its documentation policy, map, templates and agent-instructions section for approval before writing them. See [docs/setup-abdullah-docs.md](docs/setup-abdullah-docs.md).
