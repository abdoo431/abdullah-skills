# abdullah-docs: design

- **Status:** Approved by the owner on 2026-11-25
- **Date:** 2026-11-25
- **Companion skills:** `setup-abdullah-docs` (this design), `abdullah-versioning` and its setup (designed separately, after this one)
- **Repository:** public, MIT licensed

## 1. Intent

An agent skill that gives any software project a documentation discipline in which every change answers four questions, each with a fixed home:

| Question | Where the answer lives |
|---|---|
| **Why** does this exist, and why was it built this way? | A spec, or an ADR |
| **What** changed, and how? | The pull request and its commits |
| **How do we know** it works? | Tests, with a regression test for every bug |
| **When** did it ship, and in which version? | The git tag and `CHANGELOG.md` |

With those links in place, a problem can be traced from the symptom to the commit, from the commit to the decision behind it, and from the decision to the requirement.

The skill works in any agent that supports the Agent Skills format (Claude Code, Codex, GitHub Copilot, Gemini CLI, Cursor, OpenCode and others), and on any number of projects.

### Why it is needed

Rules written in one repository's policy files do not travel, and an agent forgets them in ordinary feature work, when nothing about the task looks like documentation. Two slips of that kind motivate the checks in this design:

- **A duplicate ADR number.** A branch takes the next ADR number; while it is open, the main branch gives the same number to another ADR. Nothing fails until someone notices two files named `0026-…`.
- **A changelog entry in a released section.** A merge from the main branch moves the `[Unreleased]` heading, and the branch's entry ends up under a version that has already shipped.

Both are mechanical, and both are caught by a check that compares the branch with a freshly fetched main branch.

## 2. Goals, non-goals, anti-goals

**Goals**

1. Follow a project's own documentation policy when it has one, and a default policy when it does not.
2. Set up documentation in an existing project that has none, without inventing facts.
3. Make the routine steps mechanical: numbering and indexing ADRs, placing changelog entries, checking links and code paths, filling the definition-of-done checklist.
4. Capture decisions made in conversation before they are lost.

**Non-goals**

- Writing design specs or implementation plans. Spec-writing skills (for example `superpowers:brainstorming` and `superpowers:writing-plans`) do that. This skill fixes where those documents live and how they are named, checks that code still matches them, and requires an ADR when code deviates.
- Versioning, releases and tags: `abdullah-versioning` owns them (§10).
- A domain glossary. A dedicated skill does it well (for example `domain-modeling` in [mattpocock/skills](https://github.com/mattpocock/skills)); this skill links to a project's glossary when one exists.
- Generated references (OpenAPI, schema docs). The policy records that they are generated, never handwritten; generating them is project work.
- Running in a project's CI. The scripts stay inside the skill (D4).

**Anti-goals** (it works, but it failed)

- It overrides a project's written rules with its own defaults.
- It writes files in a project, or edits its agent instructions, without the owner seeing and approving them.
- It creates empty or placeholder documents to complete a set.
- It writes plausible but unverified history into a retroactive ADR.
- It deletes or rewrites an ADR or spec instead of superseding or amending it.

## 3. Constraints

- **English only.** Documents the skill writes by default are in English. This is the skill's default policy; a project whose policy requires other languages keeps its rule (C1).
- **Harness-neutral text.** `SKILL.md` files follow the Agent Skills format (YAML front matter with `name` and `description`, Markdown body). Procedure text names no tool specific to one agent. A dependency on another skill is written as "call the Skill tool with `<name>`", not as a `/name` mention.
- **Real files, no symlinks inside the repository.** Plugin installers copy the tree and drop symlinks.
- **Scripts:** Python 3.10 or later, standard library only, cross-platform. They take paths as arguments, never assume the current directory is the repository root, and locate their own templates relative to their own file.
- **Read-only by default.** Checks never modify files. Only `new_adr.py` writes, and only the new ADR and its index row.
- **Git-aware, not git-dependent.** Without git or a remote, scripts fall back to local state and say so.

## 4. Decisions

The owner's decisions:

| # | Decision |
|---|---|
| D1 | Separate skills for documentation and for versioning. `CHANGELOG.md` is the shared boundary (§10). |
| D2 | English-only documentation is the skill's default, not a change to any project's policy. |
| D3 | Two profiles, chosen per project: `lean` and `full` (§7). |
| D4 | The scripts live in the skill only. They are not copied into projects. |
| D5 | Version 1 includes `new_adr.py`, `check_docs.py` (code-path checks limited to paths), `pr_checklist.py` and decision capture. |
| D6 | The done check and decision capture are made reliable by a section in the project's agent instructions (§6.5), written by the setup with the owner's agreement. The skill's description also triggers on documentation work, before a pull request, and when a task is declared done. |
| D7 | The skills work in Claude Code and in every other agent that supports Agent Skills, and are published in their own public GitHub repository. |
| D8 | Setup is its own user-invoked skill, `setup-abdullah-docs`. When `abdullah-docs` runs in a project that has not been set up, it starts the setup itself. |
| D9 | The repository is `abdoo431/abdullah-skills` on GitHub. The build ends with it published, a first release `v0.1.0`, and every install route run once. Before the publishing step, the owner reviews everything that will be made public. |

Calls made by the designer, open to correction:

| # | Call | Reason |
|---|---|---|
| C1 | A project's written policy wins over the skill's defaults. The skill may propose a change to a project rule but never applies it on its own. | A project's rules exist for its own reasons. |
| C2 | With no recorded profile, the default is `lean`. | It creates less that nobody maintains. |
| C3 | The profile is recorded in the project's policy document as a line, `Documentation profile: lean`. | One place, readable by people and agents. |
| C4 | Decision capture is a procedure in `SKILL.md`, not a script. | It reads the conversation, which a script cannot. |
| C5 | Checks cover the files changed since the base by default; `--all` audits everything. Documents that are history (released changelog sections, superseded ADRs, plans, and anything the project's policy says is never edited) give warnings, not failures. | A stale path in a document nobody may edit is not a problem anyone can fix, and a plan names files that do not exist yet. |
| C6 | `check_docs.py --release` skips the "added outside `[Unreleased]`" rule. The agent passes it on the project's release and hotfix branches. | Moving entries into a version section is the point of a release. |
| C7 | Scripts never fetch. The agent runs `git fetch` before `new_adr.py` and before the done check. When the check finds this branch's ADR number taken on the base, the agent renumbers this branch's ADR (file name, title line, index row, inbound links) and says so. | The base's ADR is already merged and linked from elsewhere, so this branch's moves. Only a fresh base catches the collision in §1. |
| C8 | A project with documentation but no policy keeps its layout (for example `doc/adr`, `docs/decisions`, three-digit numbers, a list index). Setup writes a policy that describes that layout and never moves files without the owner's agreement. `new_adr.py` handles a table index and a list index, and refuses any other with a clear message. | Follows C1. |
| C9 | The setup procedure lives in `abdullah-docs` (`reference/setup.md`). `setup-abdullah-docs` is a thin user-invoked entry point that calls the Skill tool with `abdullah-docs` and runs that procedure. | A user-invoked skill cannot be invoked by another skill in any harness, so the shared procedure must belong to the model-invoked one for D8's automatic start to work. One copy of the procedure. |
| C10 | The automatic setup starts on its own but writes nothing until the owner has seen the drafts and agreed. If the owner declines, the task continues on the default `lean` rules, and the setup is not offered again in that session. | Anti-goal: no project files written without approval. |
| C12 | `new_adr.py` uses the project's ADR template when one exists (`<adr-dir>/0000-template.md` or `<adr-dir>/template.md`), and the skill's own template otherwise. Setup writes a template into the project only when it has none; a re-run never overwrites one, it shows the difference from the skill's current template and asks. | Follows C1: a template the owner edited is a project rule. |
| C13 | The policy carries the check settings in one fenced block, next to the profile line, which setup writes and the scripts read with `--policy docs/DOCUMENTATION.md`. Flags on the command line override it. | Each session would otherwise re-derive `--adr-dir`, `--pairs`, `--history` and `--base` from prose and could get different results. It is part of the policy document, not a separate configuration file, so D4 holds. |
| C14 | The agent section is present when `CLAUDE.md` or `AGENTS.md` has the heading `## Documentation (abdullah-docs)`. Setup always writes the heading; when the file already says some of it in other words, the section under the heading holds only the missing lines. | One mechanical test for §6.1 and `check_docs.py`, with no duplicated rules and no repeated offers. |
| C15 | The mature-project test in §12 runs read-only on a private repository on the owner's machine that has a documentation policy, bilingual specs and over forty ADRs. Every finding is shown to the owner. | A real repository is the only good test of false positives; read-only, nothing in it changes. |
| C11 | In the `lean` profile an ADR is written only when the decision is hard to reverse, surprising without context, and the result of a real trade-off, and it may be a single paragraph. In `full`, the policy's broader trigger and the full template apply. | Keeps a small project's ADRs few and worth reading. The three-part test comes from mattpocock/skills' `domain-modeling`. |

## 5. The skills

| Skill | Invocation | Job |
|---|---|---|
| `abdullah-docs` | Model-invoked: the agent reaches for it, or the user types it | The daily discipline: §6.1 to §6.6, the scripts, decision capture, and the setup procedure it owns (C9) |
| `setup-abdullah-docs` | User-invoked only | Runs the setup procedure on request: first setup, or re-running it to refresh |

`setup-abdullah-docs` carries `disable-model-invocation: true` in its front matter and `policy.allow_implicit_invocation: false` in `agents/openai.yaml`, so no agent fires it on its own. `abdullah-docs` carries neither, so its description triggers it.

## 6. Behavior

### 6.1 First step on every task: is the project set up?

From the repository root, the skill looks for:

- a documentation policy: `docs/DOCUMENTATION.md`, `DOCUMENTATION.md`, or a "Documentation" section in `CONTRIBUTING.md`;
- the skill's section in `CLAUDE.md` or `AGENTS.md` (§6.5);
- a documentation map: `docs/README.md`.

| Found | Then |
|---|---|
| A policy and the section | Set up. Apply the policy; the skill's defaults fill only what it leaves unsaid. Read the profile line (C3). |
| A policy, no section | Offer to add the section only (§6.5), then continue. |
| Documentation, no policy | Start the setup (C10), which adopts the existing layout (C8). |
| Nothing | Start the setup (C10). |

### 6.2 Tasks

| Task | Trigger | What the skill does |
|---|---|---|
| New ADR | A decision that meets the profile's test (C11); a deviation from an approved spec; a decision taken in chat | Fetches, runs `new_adr.py`, fills the sections, links the ADR from the related README, changelog entry and commit `Refs:` where the project uses them |
| Supersede or amend | A later decision replaces or changes an earlier one | Never deletes. Sets `Status: Superseded by [NNNN](…)`, or adds "amended by NNNN" to the old ADR's status line |
| Changelog entry | A user-visible or behavioral change | Adds it under `[Unreleased]`, in the right Keep a Changelog subsection (Added, Changed, Deprecated, Removed, Fixed, Security) |
| Spec deviation | Code must differ from an approved spec | Updates the spec (every language version the project requires) or writes an ADR, in the same change |
| Incident record | A bug found in a demo or release, or one that took more than an hour to diagnose | Writes it from the template, links it from the fix commit and the changelog entry |
| Runbook | A new operational procedure | Writes it in `docs/runbooks/` |
| Project README | A new project or package; a change to its public interface | Creates or updates it |
| Decision capture | The end of a session, or when asked | §8 |
| Done check | The end of any task that touched code or docs; before a pull request | Fetches, runs `check_docs.py` and `pr_checklist.py`, fixes what they report, and lists each checklist item's status in its final message |

### 6.3 Setup

Setup runs from `setup-abdullah-docs`, or on its own from `abdullah-docs` (§6.1). The procedure, in `reference/setup.md`:

1. **Survey, read-only.** Languages and build files, top-level structure, entry points, scripts, CI configuration, existing READMEs and documentation, `CLAUDE.md` and `AGENTS.md`, and `git log` (first commit, major merges, dependency changes).
2. **Present findings and ask the profile**, `lean` or `full`, recommended answer first (§7).
3. **Show the drafts:** the policy (adapted from the default, carrying the profile line), the map, the agent-instructions section, and the list of documents it would write. The owner can edit before anything is written.
4. **Write the skeleton** for the profile: `docs/DOCUMENTATION.md`, `docs/README.md`, the ADR index and template, `CHANGELOG.md` with `[Unreleased]`, and the templates the profile needs.
5. **Write what the code shows:**
   - an architecture overview when the project has more than one component;
   - retroactive ADRs for the major decisions the code makes visible (framework, database, architecture style, dependencies with lock-in). Each says in its status line that it was recorded retroactively, and on which date. Its context comes from the code and git history only;
   - a runbook for building, running and testing, taken from the scripts and build files that exist.
6. **Never invent.** A fact the code and history do not show is written as `> Needs confirmation: <question>` in place. The setup ends with the full list of these questions.
7. **Add the section** (§6.5) to `CLAUDE.md` and `AGENTS.md`, whichever exist (both when both do). When neither exists, ask which to create.
8. **Deliver as one change** on a `docs/<name>` branch, or the project's equivalent, as a pull request where the project uses them.

Re-running the setup on a project that is already set up refreshes the section and templates and reports what changed. It never rewrites the project's policy without showing the diff.

### 6.4 The default policy

`reference/policy-default.md` holds the policy that setup adapts. It keeps:

- the four questions and where each answer lives (§1);
- specs are the source of truth; a deviation needs a spec update or an ADR in the same change;
- decisions are recorded, not remembered;
- nothing is deleted; superseded documents say so;
- docs live in the repository; external tools receive copies only;
- ISO dates (`YYYY-MM-DD`) and lower-kebab-case file names;
- code comments explain why, not what; public contracts carry doc comments;
- the definition-of-done checklist;
- the tracing procedure from symptom to decision.

Spec and plan locations follow the spec-writing skill the project uses; by default `docs/superpowers/specs/` and `docs/superpowers/plans/`.

### 6.5 The section in the project's agent instructions

Both slips in §1 happen during ordinary feature work, when nothing loads a documentation skill. The trigger therefore lives where every session reads it (D6). The section is the same in every project, apart from the policy path:

```markdown
## Documentation (abdullah-docs)

This project follows the policy in docs/DOCUMENTATION.md, using the abdullah-docs skill
(https://github.com/abdoo431/abdullah-skills).
- Before calling any task done, and before opening a pull request, run its done check.
- At the end of a session, run its decision capture.
- If your agent cannot load skills, install them from the link above.
```

It names no path on the machine, because each agent installs skills in its own place. If the file already says the same in other words, the section adds only the lines that are missing. The done check reports when the section is absent.

## 7. Profiles

| Document | `lean` | `full` |
|---|---|---|
| Documentation map `docs/README.md` | Always | Always |
| `CHANGELOG.md` | Always | Always |
| ADRs `docs/adr/` with index and template | Always; ADRs only by the three-part test (C11) | Always; ADRs by the policy's broader trigger, full template |
| Runbook: build, run, test | Always | Always |
| README per project or package | Always | Always |
| Architecture overview | When there is more than one component | At setup |
| Specs and plans | When the first major feature is designed | Directories and naming set at setup |
| Incident records | At the first qualifying bug | Template at setup |
| Other runbooks | At the first such procedure | Template at setup |

`full` sets up every type at setup, but still writes no document without content: it creates directories, templates and index files, not empty documents.

## 8. Decision capture

At the end of a session, or when asked, the agent reviews the conversation for decisions: a choice between options, a rule the owner set, an agreed deviation. For each it checks whether a spec or ADR already records it. It lists the unrecorded ones, each with a proposed home (a spec section, or a new ADR if it meets the profile's test), and writes them only after the owner agrees.

## 9. Scripts

In `skills/abdullah-docs/scripts/`. Each has `--help`, exits 0 when clean, 1 when it found problems, and 2 on a usage error. Findings are one per line, `path:line: severity: kind: message`, with `severity` either `error` or `warning`, so the agent can act on each. Only errors change the exit code. `new_adr.py` prints only the new path on stdout and its warnings on stderr.

### 9.1 `new_adr.py`

```
new_adr.py --root <repo> --title "<decision title>" [--adr-dir docs/adr] [--base origin/main] [--short]
```

- The number is one more than the highest found in the ADR directory locally **and** on the base ref (`git ls-tree`; default: the remote's default branch).
- Writes `NNNN-<kebab-title>.md` with today's date and `Status: Proposed`, from the full template, or the one-paragraph template with `--short` (C11). Adds a row to the index in number order (table or list, C8).
- Prints the new file's path. Without git or the base ref, it uses local numbers and warns.

### 9.2 `check_docs.py`

```
check_docs.py --root <repo> [--base origin/main] [--all] [--release] [--adr-dir docs/adr]
              [--changelog CHANGELOG.md] [--pairs "<glob>.md:<glob>.en.md"] [--history "<glob>"]...
```

Checks the files changed since `--base` by default; `--all` checks every document (C5).

| Check | Fails when |
|---|---|
| ADR index | An ADR file is missing from the index, or an index row names a missing file |
| ADR numbers | Two ADRs share a number, locally or against the base ref |
| ADR header | An ADR has no status or date; a `Superseded by` link points to a missing ADR |
| Links | A relative Markdown link points to a missing file. Anchors are checked against headings and reported as warnings |
| Code paths | A backticked or linked repository path (has `/` and an extension; not a URL; no `<`, `>` or `*`) does not exist. Paths only (D5) |
| Changelog | There is no `[Unreleased]` section; or a line added since the base lies outside it, unless `--release` (C6) or the line sits in a version section whose heading the branch also adds (a release) |
| Pairs | With `--pairs`, a document has no counterpart in the other language, or one changed since the base and its counterpart did not. Off by default, for projects whose policy requires translations |
| Agent section | Neither `CLAUDE.md` nor `AGENTS.md` carries the section (§6.5). A warning |

`--history` adds globs whose link, anchor and code-path findings are warnings (C5); ADR findings stay errors everywhere. `--policy` reads the settings block from the project's policy (C13); without it the scripts find the policy as §6.1 does (`docs/DOCUMENTATION.md`, `DOCUMENTATION.md`, or a `CONTRIBUTING.md` with a `## Documentation` heading). Flags override the block. `examples` lists files whose backticked paths describe other projects (a skill's reference pages, a README), which the code-path check skips. There is no separate configuration file (D4). The block, written by setup:

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

### 9.3 `pr_checklist.py`

```
pr_checklist.py --root <repo> --base origin/main
```

Reads the diff against the base and prints each definition-of-done item with what the diff shows: changelog touched or not, spec, plan or ADR files touched, tests touched, a new runbook, whether any source file changed. It decides nothing; the agent uses it to fill the PR template honestly and to report each item's status.

## 10. Boundaries with other skills

- **Spec-writing skills** write specs and plans; this skill gives their locations and names and checks code against them.
- **`abdullah-versioning`** owns the version scheme, where the version is declared, releases, tags, and moving `[Unreleased]` into a version section. This skill writes `[Unreleased]` entries during normal work. Both use Keep a Changelog, and each refers to the other instead of repeating it. Whether entries should be written as separate fragment files that a release collects (the changesets pattern, which also prevents the misplaced entry in §1) is a question for that design.
- **A glossary skill**, when installed, owns `GLOSSARY.md`. This skill only links to it.

## 11. The repository

Public, MIT licensed, laid out after [mattpocock/skills](https://github.com/mattpocock/skills):

```
abdullah-skills/
├── README.md                       the problem each skill fixes, installation, the skill list by invocation
├── LICENSE                         MIT
├── CHANGELOG.md
├── CONTRIBUTING.md                 how to report a problem
├── CLAUDE.md, AGENTS.md            identical: the rules for maintaining this repository
├── .agents/
│   ├── install-block.md            the one wording of the install commands; README copies it verbatim
│   ├── writing-docs.md             the template for the pages in docs/
│   └── adr/                        this repository's own decisions
├── .claude-plugin/
│   ├── plugin.json                 name, version, and the skills array
│   └── marketplace.json            this repository as its own marketplace
├── .github/workflows/check.yml     front matter, script tests, plugin version in sync
├── docs/
│   ├── abdullah-docs.md            the human-facing page for each skill
│   ├── setup-abdullah-docs.md
│   └── design/                     design documents, this one included
├── scripts/
│   ├── check_frontmatter.py        every SKILL.md parses and has name and description
│   └── link_skills.py              maintainer only: link the working copy into local agent skill directories
└── skills/
    ├── abdullah-docs/
    │   ├── SKILL.md
    │   ├── agents/openai.yaml      display name and short description for Codex
    │   ├── reference/              setup.md, policy-default.md, adr.md, changelog.md, incident.md, runbook.md, readme.md
    │   ├── templates/
    │   ├── scripts/                new_adr.py, check_docs.py, pr_checklist.py
    │   └── tests/                  unittest, with fixture repositories
    └── setup-abdullah-docs/
        ├── SKILL.md                disable-model-invocation: true
        └── agents/openai.yaml      policy.allow_implicit_invocation: false
```

This document moves to `docs/design/` when the repository is created.

### 11.1 Installation

Managed installs first, each updating itself; manual routes after, labelled as such. The wording lives once in `.agents/install-block.md`.

| Agent | Route | Updates itself |
|---|---|---|
| Claude Code | `claude plugin marketplace add abdoo431/abdullah-skills`, then `claude plugin install abdullah-skills@<marketplace>` | Yes |
| Codex | `codex plugin marketplace add abdoo431/abdullah-skills`, then `codex plugin add abdullah-skills@<marketplace>` | Yes, at startup |
| GitHub Copilot CLI and VS Code | The same marketplace | Yes, after a one-time opt-in |
| Gemini CLI | `gemini skills install https://github.com/abdoo431/abdullah-skills.git --path skills` | No |
| Any other agent | `npx skills@latest add abdoo431/abdullah-skills` | No: `npx skills@latest update` |

Every route is run once against the published repository before the README promises it; a route nobody has run is listed as untested.

### 11.2 The docs pages

One page per skill in `docs/`, in a fixed order: **What it does** (the job, and the one fact that makes the skill behave differently from the obvious default), **When to reach for it** (who invokes it, and where it ends and a neighbouring skill begins), **Prerequisites** (only when there are any), one to three sections in the skill's own vocabulary, **Common questions** (real questions only, sized to the evidence), **It's working if** (signals a reader can check without opening `SKILL.md`), and **Where it fits**. `.agents/writing-docs.md` holds the template.

### 11.3 Versions

The repository has one version, in `.claude-plugin/plugin.json`, because plugin installs update only when that version changes. `abdullah-versioning` will manage it once it exists; until then the version is bumped by hand with each release and tagged `vX.Y.Z`.

## 12. How it is verified

- **Scripts:** unit tests on small fixture repositories: an index missing a row, a duplicate number on the base ref, a broken link, a changelog line outside `[Unreleased]`, a missing language pair, a list-style index, a clean repository.
- **The repository:** `check_frontmatter.py` and the script tests run in GitHub Actions on every pull request; `claude plugin validate . --strict` passes.
- **On a mature project (C15):** on a real repository that already has a documentation policy, bilingual specs and many ADRs, `check_docs.py --all` reports only real problems, each confirmed by hand; `new_adr.py` on a branch cut before the latest ADR gives the number after the highest on the main branch.
- **On a project with no docs:** the automatic setup runs on a small sample project, shows its drafts before writing, and produces the `lean` skeleton, retroactive ADRs marked as such, the agent section, and a list of "Needs confirmation" questions, with no invented facts.
- **Installation:** each route in §11.1 is run once against the published repository.

## 13. Left to the builder

- The exact wording of each `description`, within D6 for `abdullah-docs`; human-facing and free of trigger phrases for `setup-abdullah-docs`.
- Template wording.
- How `check_docs.py` parses Markdown links and backticked paths (a careful regex; no Markdown library) and slugifies anchors (GitHub's rules).
- The marketplace name in `marketplace.json`.
