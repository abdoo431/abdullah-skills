# 0001. Skills and install routes

- **Status:** Accepted
- **Date:** 2026-11-25
- **Deciders:** The repository owner
- **Related:** [Design §11](../../docs/design/2026-11-25-abdullah-docs-design.md#11-the-repository), decisions D7 and D9 of the [design](../../docs/design/2026-11-25-abdullah-docs-design.md#4-decisions)

## Context

The skills must work in Claude Code and in every other agent that supports the Agent Skills format, and on any number of projects (D7). Rules kept in one project's files do not travel, so the skills need a home of their own that any project can install from.

Each agent installs skills its own way. Claude Code, Codex and GitHub Copilot install plugins from a marketplace and update them; Gemini CLI installs skill folders from a git repository; other agents can use `npx skills`, which copies the folders. Plugin installers copy the tree and drop symbolic links, so every skill must be a real folder. A plugin install updates only when the plugin's version changes.

[mattpocock/skills](https://github.com/mattpocock/skills) already solves the same problem for a set of public skills: one repository, one folder per skill under `skills/`, the repository acting as its own plugin and marketplace, and a README that lists the skills and the install commands. It is the prior art this layout follows.

## Decision

The skills live in one public repository, `abdoo431/abdullah-skills`, laid out after mattpocock/skills: each skill is a real folder `skills/<name>/` with its `SKILL.md`; the repository is its own plugin (`.claude-plugin/plugin.json`, with the one version) and its own marketplace (`.claude-plugin/marketplace.json`, named `abdullah`). The install commands are worded once, in `.agents/install-block.md`, and copied verbatim into the README and the agent instructions: managed routes first, manual routes after, each marked untested until it has been run against the published repository.

## Alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| Keep the skills in a private project or a personal skills folder | Nothing to publish or maintain | The rules do not travel to other projects or agents, which is the problem D7 fixes |
| One repository per skill | Each skill versioned on its own | `setup-abdullah-docs` cannot work without `abdullah-docs` (ADR 0002), so they would always be installed together; two marketplaces to keep in step |
| One manual route (`npx skills`) for every agent | One set of instructions | No self-updating install in Claude Code, Codex or Copilot |
| Share files between skills through symbolic links | No duplicated files | Plugin installers drop symbolic links, so installed skills would break |

## Consequences

- Each agent installs with its own managed route where one exists, and managed installs update themselves.
- The install wording has one source; a repository test checks that every copy carries it verbatim.
- Every release must bump `version` in `.claude-plugin/plugin.json`, or plugin installs never see it.
- A route is promised as tested only after it has been run against the published repository, so the README changes when routes are tested.
- A future skill, such as `abdullah-versioning`, is added as another folder under `skills/` and another entry in the plugin's `skills` list.
