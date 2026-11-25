# 0003. Plugin validation without strict mode at the repository root

- **Status:** Accepted
- **Date:** 2026-11-25
- **Deciders:** The repository owner
- **Related:** Deviates from [design §12](../../docs/design/2026-11-25-abdullah-docs-design.md#12-how-it-is-verified) ("`claude plugin validate . --strict` passes"); keeps the layout of [design §11](../../docs/design/2026-11-25-abdullah-docs-design.md#11-the-repository) and [ADR 0001](0001-skills-and-install-routes.md)

## Context

Design §12 says the repository is verified with `claude plugin validate . --strict`. The repository is its own plugin: the marketplace lists it with `source: "./"`, so the plugin root is the repository root, and design §11 puts `CLAUDE.md` and `AGENTS.md` there. The validator warns about it:

> CLAUDE.md at the plugin root is not loaded as project context. To ship context with your plugin, use a skill (skills/<name>/SKILL.md) instead.

`--strict` turns every warning into a failure, so the strict run fails on this warning alone. The warning is true but does not apply: our `CLAUDE.md` holds the rules for maintaining this repository, read by agents working in a clone, not context meant for people who install the plugin. The plugin's content is its skills, which validate without findings. `claude plugin validate .claude-plugin/marketplace.json --strict` passes, and `claude plugin validate .` passes with this one warning. (Its separate plugin directory checks, for the catalog plugins are submitted to, also report a missing icon; they do not change the result, and the strict run does not fail on them.)

## Decision

Keep the layout. Verify the repository with `claude plugin validate .claude-plugin/marketplace.json --strict`, which must pass, and `claude plugin validate .`, which must pass with the `CLAUDE.md` warning above as its only warning. The agent instructions quote the expected warning so a maintainer can compare.

## Alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| Move the plugin into a subfolder (for example `plugins/abdullah-skills/`) and point the marketplace's `source` there | `validate --strict` on the plugin passes | Breaks the layout after mattpocock/skills (ADR 0001); the Gemini CLI route installs from `--path skills`, so the skills would move and the manual install routes would change with them |
| Drop `CLAUDE.md` and keep only `AGENTS.md` | Clears the warning | Claude Code reads `CLAUDE.md`, not `AGENTS.md`, so maintainers using it lose the rules; design §11 keeps both, identical |
| Accept the warning, and run strict on the marketplace manifest only | No layout change; the manifests are still checked strictly | A new warning on the plugin is not caught by a strict run; a maintainer compares the non-strict output with the quoted warning |

## Consequences

- The layout of design §11 stays as it is.
- The manifests are still checked strictly, through the marketplace manifest.
- A new warning on the plugin does not fail a command by itself: the maintainer must compare the non-strict output with the expected warning, as the agent instructions say.
- If the validator gains a way to exclude a file, or stops warning about a maintainer `CLAUDE.md`, `claude plugin validate . --strict` can return, superseding this ADR.
