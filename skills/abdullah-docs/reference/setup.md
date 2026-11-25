# Setup

Setup gives a project a documentation policy, a documentation map, the files its profile needs, and a section in its agent instructions. It runs when the owner invokes `setup-abdullah-docs`, or on its own when step 0 of [SKILL.md](../SKILL.md) finds no policy.

Rules for the whole procedure:

- Write nothing before the owner has seen the drafts and agreed (step 3).
- Never invent a fact. Write only what the code, the git history or the owner shows (step 6).
- Never move, rename or delete an existing document without the owner's agreement.
- If the owner declines a setup that started on its own, stop. Continue the task on the default `lean` rules, and do not offer the setup again in this session.

## The steps

### 1. Survey the project, read-only

Read, without changing anything:

1. Languages and build files (`package.json`, `pyproject.toml`, `Cargo.toml`, `go.mod`, `pom.xml`, `Makefile` and the like).
2. The top-level structure, entry points, and the scripts that build, run and test the project.
3. CI configuration.
4. Existing READMEs and documentation: ADR folders, changelog, specs, runbooks, a glossary.
5. `CLAUDE.md` and `AGENTS.md`.
6. `git log`: the first commit, major merges, and dependency changes.
7. The base branch: the remote's default branch (`git symbolic-ref refs/remotes/origin/HEAD`), usually `origin/main`.

If the project already has documentation, note its layout: the ADR folder (`doc/adr`, `docs/decisions`, `docs/architecture/decisions`), the number width (three or four digits), the index shape (a table or a list of links), the ADR template, and the changelog's headings. Setup adopts that layout (see [Adopting an existing layout](#adopting-an-existing-layout)).

### 2. Present the findings and ask for the profile

Summarize what you found in a few lines. Then ask the owner to choose a profile:

- `lean`: the map, the changelog, the ADR folder, a build-run-test runbook and READMEs. Other documents appear when they first have content. ADRs only for decisions that pass the three-part test in [adr.md](adr.md).
- `full`: everything in `lean`, plus templates for incidents and runbooks and the spec and plan locations at setup, and ADRs for every significant decision. Suits larger teams, many components, or regulated work.

Put your recommendation first and say why. Recommend `lean` unless the survey shows a reason for `full`. Without an answer, use `lean`.

The profile table is in [policy-default.md](policy-default.md#profiles).

### 3. Show the drafts

Show the owner, in full:

1. **The policy**, adapted from [policy-default.md](policy-default.md). It carries the profile line and the settings block (see [The settings block](#the-settings-block)). It describes the project's real layout. Before showing it, check that every backticked path in it either exists or will be written by this setup; a document the profile does not create yet is named without a backticked path.
2. **The map**, from [../templates/docs-map.md](../templates/docs-map.md). Keep only rows for documents that exist or that this setup will write.
3. **The agent-instructions section**, from [../templates/agent-section.md](../templates/agent-section.md), with `{policy}` replaced by the policy's path.
4. **The list of documents** this setup would write, each with the source of its content (which files or commits).

The owner can edit any draft. Write nothing until the owner agrees. If the owner declines, see the rules at the top.

### 4. Write the skeleton

First, before writing any file, create the branch the setup is delivered on: `docs/<name>` (for example `docs/documentation-setup`), or the project's equivalent. If the working tree is on another task's branch with uncommitted work, say so and ask the owner how to proceed. Do not switch branches over that work on your own.

Then write, for the chosen profile:

| File | Source | Profile |
|---|---|---|
| `docs/DOCUMENTATION.md` | The approved policy draft | Both |
| `docs/README.md` | The approved map draft | Both |
| `docs/adr/README.md` | The ADR index below, unless an index exists | Both |
| `docs/adr/0000-template.md` | [../templates/adr-full.md](../templates/adr-full.md), only when the project has no ADR template | Both |
| `CHANGELOG.md` | [../templates/changelog.md](../templates/changelog.md), only when the project has none | Both |
| `docs/incidents/template.md` | [../templates/incident.md](../templates/incident.md) | `full` |
| `docs/runbooks/template.md` | [../templates/runbook.md](../templates/runbook.md) | `full` |

Use the project's paths where it already has its own (for example `doc/adr` instead of `docs/adr`).

The ADR index, when the project has none:

```markdown
# Architecture Decision Records

| ADR | Decision | Status |
|-----|----------|--------|
```

An existing `CHANGELOG.md` without an unreleased section: propose adding `## [Unreleased]` above the first version heading, and add it only after the owner agrees.

For `full`, record the spec and plan folders and their file names in the policy and the map. Git keeps no empty folder, so the folders appear with the first spec and plan. Do not write empty documents to make them appear.

### 5. Write what the code shows

1. **An architecture overview** (`docs/architecture.md`) when the project has more than one component, or at setup in `full`. Describe the components, how they talk, and where each lives, from the code.
2. **Retroactive ADRs** for the major decisions the code makes visible: the framework, the database, the architecture style, and dependencies with lock-in. They record decisions already in force, so they are `Accepted` without a fresh decision by the owner (see [adr.md](adr.md#retroactive-adrs)). Create each with `new_adr.py`. In each:
   - set the status line to `Accepted (recorded retroactively on YYYY-MM-DD)`, with today's date, and its status in the index to `Accepted`;
   - take the context from the code and the git history only;
   - write any reason the code does not show as a `Needs confirmation` question.
3. **A runbook for building, running and testing** (`docs/runbooks/build-run-test.md`), from the scripts and build files that exist. Use [../templates/runbook.md](../templates/runbook.md). Write only commands that exist in the project.

### 6. Never invent

Write a fact the code and history do not show as a question, in place:

```markdown
> Needs confirmation: <question>
```

End the setup with the full list of these questions, each with its file.

### 7. Add the section to the agent instructions

1. Take [../templates/agent-section.md](../templates/agent-section.md) and replace `{policy}` with the policy's path.
2. Add it to `CLAUDE.md` and `AGENTS.md`, whichever exist; to both when both do. When neither exists, ask the owner which to create.
3. Always write the heading `## Documentation (abdullah-docs)`. The scripts look for that exact line.
4. When the file already says some of the section's lines in other words, put under the heading only the lines that are missing.

### 8. Deliver as one change

1. Commit everything on the branch created in step 4.
2. Run the done check from [SKILL.md](../SKILL.md#the-done-check).
3. Open a pull request where the project uses them.
4. Report what was written, the profile, and the `Needs confirmation` list.

## Re-running the setup

On a project that is already set up:

1. Create the branch as in step 4 before writing anything.
2. Never rewrite the project's policy without showing the difference first and getting the owner's agreement.
3. Never overwrite a template in the project (an ADR template, an incident or runbook template). The owner may have edited it, which makes it a project rule. Compare it with the skill's current template; when they differ, show the difference and ask whether to update it.
4. Write only what is missing: a template the profile needs that the project does not have, and the agent section's missing lines (apply step 7 again: keep the heading, add only missing lines).
5. Report what was written, what was offered, and what the owner declined.

## Adopting an existing layout

A project with documentation but no policy keeps its layout:

- The policy describes the folders, the number width, the index shape and the templates the project already uses. Set `adr-dir` to the project's ADR folder.
- Do not move or rename files without the owner's agreement. You may propose a move, with the reason.
- `new_adr.py` keeps the project's number width and handles an index that is a table or a list of links. It refuses any other index shape with a message naming the file. Then propose turning the index into a table, or add rows by hand.
- `new_adr.py` uses the project's template when the ADR folder has `0000-template.md` or `template.md`.

## The settings block

The policy carries the check settings in one fenced block, next to the profile line. The scripts read it; flags on the command line override it. This is the block setup writes, with example values:

````markdown
Documentation profile: lean

```abdullah-docs
adr-dir: docs/adr
changelog: CHANGELOG.md
base: origin/main
history: docs/superpowers/plans/**, conversations/**
pairs: docs/superpowers/specs/*-design.md:docs/superpowers/specs/*-design.en.md
examples: README.md
```
````

The keys, one per line, `key: value`. A list is comma-separated. Leave out a key to use its default.

| Key | Meaning | Default |
|---|---|---|
| `adr-dir` | The ADR folder | `docs/adr` |
| `changelog` | The changelog file | `CHANGELOG.md` |
| `base` | The branch changes are compared with | The remote's default branch |
| `history` | Globs of documents nobody edits (plans, archives, anything the policy freezes). Their link and code-path findings are warnings | None |
| `pairs` | Language pairs, `<glob>:<glob>`, for a policy that requires translations | None |
| `examples` | Files whose backticked paths describe other projects. The code-path check skips them | None |
| `specs` | The spec folder | `docs/superpowers/specs` |
| `plans` | The plan folder | `docs/superpowers/plans` |

Write `pairs` only when the policy requires documents in more than one language. Put the plans folder in `history`, because a plan names files that do not exist yet.
