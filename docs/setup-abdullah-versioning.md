# setup-abdullah-versioning

Sets up a project for `abdullah-versioning`, or refreshes an earlier setup. Source: [`skills/setup-abdullah-versioning/SKILL.md`](../skills/setup-abdullah-versioning/SKILL.md).

## What it does

It surveys the project's tags, version files, changelog and branches, tells a new project from one that already has releases, agrees the layout and the rest with you, and drafts the project's release policy and a section for its agent instructions. It writes them only after you approve.

The fact that sets it apart: **it stops and asks instead of guessing.** When the tags, the version files and the changelog disagree, when there are releases but no tags, when the tags are not SemVer, or when the repository holds several independently versioned packages, it shows you what it found and waits for your decision.

## When to reach for it

Only you start it: run `/setup-abdullah-versioning`, or `/abdullah-skills:setup-abdullah-versioning` when installed as a plugin. No agent runs it on its own. Run it once per project, and again when the project's branches or version files change.

You can also leave it to `abdullah-versioning`, which offers the same setup the first time it runs in a project without a release policy. Both run one procedure, which lives in `abdullah-versioning`, as [ADR 0002](../.agents/adr/0002-setup-owned-by-the-model-invoked-skill.md) decided for the documentation setup.

## Prerequisites

- The `abdullah-versioning` skill, installed in the same agent. The plugin install brings both. Without it, the setup tells you where to install it and stops.

## The steps

1. **Python:** checks for Python 3.10 or later and gives you the install command when it is missing.
2. **Survey, read-only:** version tags and their format, every file that declares a version, the changelog, the branches and the layout they suggest, and a verdict: new, released (with the current version), or ambiguous. The production branch is the one that holds the release tags, even when the repository's default branch is `dev`.
3. **Questions:** every disagreement or unsupported case, one by one.
4. **Choices:** the layout and branch names (a new project defaults to `dev` → `staging` → `main`), the version files, the first version (`0.1.0` unless you choose `1.0.0`), the tag format, and whether to use `alpha` and `beta`.
5. **Drafts:** `docs/RELEASING.md` for a new project (or a settings block in the release document the project already has), and the section for `CLAUDE.md` and `AGENTS.md`.
6. **Writing,** after you agree, including any missing `dev` or `staging` branch. Pushing them waits for your approval.
7. **A check** that the status matches what you chose.

## Re-running it

On a project that is already set up, it surveys again, compares with the policy, and proposes each difference: a new version file, a new branch, a changed tag format. It never overwrites the policy without asking.

## It's working if

- Nothing in the project changes before you have seen the drafts and agreed.
- The project gains a release policy with an `abdullah-versioning` settings block, and a `## Versioning (abdullah-versioning)` section in its agent instructions.
- On a project with releases, the current version it reports is the latest tag, and every version file agrees with it.
- Afterwards, `abdullah-versioning` treats the project as set up and stops offering the setup.

## Where it fits

It is the user's entry point into the setup procedure of [abdullah-versioning](abdullah-versioning.md), which does the releases once the project is set up. [setup-abdullah-docs](setup-abdullah-docs.md) is its counterpart for documentation.
