# setup-abdullah-docs

Sets up a project for `abdullah-docs`, or refreshes an earlier setup. Source: [`skills/setup-abdullah-docs/SKILL.md`](../skills/setup-abdullah-docs/SKILL.md).

## What it does

It surveys the project, asks you to choose a profile, drafts the project's documentation policy, its documentation map, its templates and a section for its agent instructions, and writes them after you approve. Where the project already has documentation, it keeps that layout and writes a policy that describes it.

The fact that sets it apart: **it never invents.** Every fact it writes comes from the code, the git history or you. Anything else is written in place as `> Needs confirmation: <question>`, and the setup ends with the full list of those questions.

## When to reach for it

Only you start it: run `/setup-abdullah-docs`, or `/abdullah-skills:setup-abdullah-docs` when installed as a plugin. No agent runs it on its own. Run it once when you start using `abdullah-docs` in a project, and again later to refresh the section and templates.

You can also leave it to `abdullah-docs`, which offers the same setup the first time it runs in a project without a documentation policy. Both run one procedure, which lives in `abdullah-docs` (see [ADR 0002](../.agents/adr/0002-setup-owned-by-the-model-invoked-skill.md)).

## Prerequisites

- The `abdullah-docs` skill, installed in the same agent. The plugin install brings both. Without it, the setup tells you where to install it and stops.

## The steps

1. **Survey, read-only:** languages and build files, structure, scripts, CI, existing documentation, `CLAUDE.md` and `AGENTS.md`, and the git history.
2. **The profile:** you choose `lean` or `full`, with a recommendation first. Without an answer, `lean`.
3. **The drafts:** the policy, the map, the agent-instructions section, and the list of documents it would write, each with where its content comes from. You can edit any of them.
4. **The skeleton,** on its own branch: the policy, the map, the ADR index and template, a changelog with `[Unreleased]`, and the templates `full` needs.
5. **What the code shows:** an architecture overview when there is more than one component, retroactive ADRs for the major decisions the code makes visible (marked as recorded retroactively), and a runbook for building, running and testing.
6. **The section** in `CLAUDE.md` and `AGENTS.md`, under the heading `## Documentation (abdullah-docs)`.
7. **One change:** everything is committed together, checked, and opened as a pull request where the project uses them.

## Re-running it

On a project that is already set up, it writes only what is missing: a template the profile needs, or lines missing from the agent section. It never rewrites your policy without showing you the difference first, and never overwrites a template you may have edited; it shows the difference from its current template and asks.

## It's working if

- Nothing in the project changes before you have seen the drafts and agreed.
- The project gains `docs/DOCUMENTATION.md` with a `Documentation profile:` line, `docs/README.md`, an ADR index and a `CHANGELOG.md` with `[Unreleased]`, on a branch of their own.
- Retroactive ADRs say on their status line that they were recorded retroactively, and on which date.
- The setup's final message lists every `Needs confirmation` question with its file.
- Afterwards, `abdullah-docs` treats the project as set up and stops offering the setup.

## Where it fits

It is the user's entry point into the setup procedure of [abdullah-docs](abdullah-docs.md), which does the daily work once the project is set up.
