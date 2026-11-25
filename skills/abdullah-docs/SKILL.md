---
name: abdullah-docs
description: "Keep a project's documentation traceable: ADRs, changelog, specs, runbooks, incident records and READMEs, under the project's own documentation policy. Use when writing or changing any of these, when a decision is made, before opening a pull request, and before calling a task done."
---

# abdullah-docs

Every change in a project should answer four questions, each in a fixed place:

| Question | Where the answer lives |
|---|---|
| Why does this exist, and why was it built this way? | A spec, or an ADR |
| What changed, and how? | The pull request and its commits |
| How do we know it works? | Tests, with a regression test for every bug |
| When did it ship, and in which version? | The git tag and `CHANGELOG.md` |

This skill keeps those links in place. Paths below are relative to this skill's folder (the folder that holds this file).

## Rules that always apply

- The project's written policy wins over this skill's defaults. You may propose a change to a project rule; never apply it on your own.
- Never write files in a project, or edit its agent instructions, before the owner has seen and approved them.
- Never create an empty or placeholder document to complete a set.
- Never invent facts. Write what the code, the history or the owner shows. Mark anything else as `> Needs confirmation: <question>`.
- Never delete or rewrite an ADR or spec. Supersede or amend it.
- Write documents in English, unless the project's policy requires other languages.
- Specs and plans are written by spec-writing skills. This skill fixes where they live and checks that code still matches them.

## Step 0: is the project set up?

Do this first on every task. From the repository root, look for:

1. A documentation policy: `docs/DOCUMENTATION.md`, `DOCUMENTATION.md`, or a `## Documentation` section in `CONTRIBUTING.md`.
2. The heading `## Documentation (abdullah-docs)` in `CLAUDE.md` or `AGENTS.md`.
3. A documentation map: `docs/README.md`.

| Found | Then |
|---|---|
| A policy and the section | The project is set up. Apply its policy; this skill's defaults fill only what it leaves unsaid. Read the `Documentation profile:` line (no line means `lean`). |
| A policy, no section | Offer to add the section only (step 7 of [reference/setup.md](reference/setup.md)), then continue the task. If the owner declines, do not offer it again in this session. |
| Documentation, no policy | Start the setup. It adopts the existing layout. |
| Nothing | Start the setup. |

"Documentation" means any of: a `docs/` or `doc/` folder, ADR files, a `CHANGELOG.md`, runbooks.

### Starting the setup on your own

1. Tell the owner the project has no documentation policy, and that you will survey it and show drafts before writing anything.
2. Follow [reference/setup.md](reference/setup.md) from step 1.
3. Write nothing until the owner has seen the drafts and agreed.
4. If the owner declines, continue the task on the default `lean` rules of [reference/policy-default.md](reference/policy-default.md). Do not offer the setup again in this session. The owner can run it later with `/setup-abdullah-docs` (listed as `/abdullah-skills:setup-abdullah-docs` when installed as a plugin).

## Tasks

| Task | When | What to do |
|---|---|---|
| New ADR | A decision that meets the profile's test; a deviation from an approved spec; a decision taken in chat | [reference/adr.md](reference/adr.md) |
| Supersede or amend an ADR | A later decision replaces or changes an earlier one | [reference/adr.md](reference/adr.md) |
| Changelog entry | A user-visible or behavioral change | [reference/changelog.md](reference/changelog.md) |
| Spec deviation | Code must differ from an approved spec | In the same change, update the spec (every language version the project requires) or write an ADR: [reference/adr.md](reference/adr.md) |
| Incident record | A bug found in a demo or release, or one that took more than an hour to diagnose | [reference/incident.md](reference/incident.md) |
| Runbook | A new operational procedure | [reference/runbook.md](reference/runbook.md) |
| Project README | A new project or package; a change to its public interface | [reference/readme.md](reference/readme.md) |
| Decision capture | The end of a session, or when asked | [reference/decisions.md](reference/decisions.md) |
| Done check | The end of any task that touched code or docs; before a pull request | [The done check](#the-done-check), below |
| Setup | Step 0 says so, or the owner asks | [reference/setup.md](reference/setup.md) |

The default policy, with the `lean` and `full` profiles and the definition of done, is in [reference/policy-default.md](reference/policy-default.md). The project's own policy overrides it.

## Running the scripts

The scripts are in this skill's `scripts/` folder. Run them with Python 3.10 or later:

```
python <this skill's folder>/scripts/<name>.py --root <repo> [--policy <policy file>]
```

- Pass `--policy` with the project's policy file when it is not in one of the places step 0 lists. The scripts read the settings block in the policy (ADR folder, changelog, base branch, history, language pairs). Flags on the command line override it.
- Exit codes: 0 clean, 1 errors found, 2 usage error.
- Findings are one per line: `path:line: severity: kind: message`. Severity is `error` or `warning`. Only errors change the exit code.
- The scripts never fetch. Run `git fetch` first, so the base branch is current.
- A `warning: base` finding means there is no usable base branch. The script then checks local state only (`check_docs.py` checks every file). Say so in your report.

| Script | Does |
|---|---|
| `new_adr.py --title "<title>" [--short]` | Writes the next-numbered ADR and its index row. Prints only the new path; warnings go to stderr |
| `check_docs.py [--all] [--release]` | Read-only check of the files changed since the base, or every file with `--all` |
| `pr_checklist.py` | Prints what the diff shows for each definition-of-done item. Decides nothing |

If Python is not available (try `python`, `python3`, then `py -3`), do the same steps by hand, and say in your final message that the scripts did not run.

## The done check

Run it at the end of every task that touched code or docs, and before opening a pull request.

1. Run `git fetch` for the base branch's remote. If it fails, continue and say so.
2. Run `check_docs.py --root <repo>` with `--policy` when needed. Add `--release` on the project's release and hotfix branches, where moving entries out of `[Unreleased]` is the point.
3. Fix every `error` finding. What each kind means:
   - `adr-number`: this branch's ADR number is taken. Renumber this branch's ADR ([reference/adr.md](reference/adr.md#renumber-after-a-collision)) and say so.
   - `adr-index`, `adr-header`, `adr-name`: the ADR folder and its index disagree, or an ADR lacks a status or date line.
   - `link`: a relative link points to a missing file. `anchor` (a warning): no heading matches the link's `#anchor`.
   - `code-path`: a backticked or linked repository path does not exist.
   - `changelog`: no `[Unreleased]` section, or a line was added below it ([reference/changelog.md](reference/changelog.md)).
   - `pair`: a document lacks its counterpart in the other language, or changed without it.
   - `agent-section` (a warning): neither `CLAUDE.md` nor `AGENTS.md` has the section. Offer it once, as in step 0.
4. Run `check_docs.py` again until it reports no errors. Fix warnings in files you changed; list the rest.
5. Run `pr_checklist.py --root <repo>`. Use its lines to fill the pull request template honestly.
6. In your final message, list each definition-of-done item with its status: done (where), not needed (why), or missing.

The items `pr_checklist.py` prints:

| Item | Done when |
|---|---|
| `spec-or-adr` | A spec or ADR records the change's reason, or the change needs none (say why) |
| `changelog` | A user-visible or behavioral change has an `[Unreleased]` entry |
| `public-interface` | Changed public interfaces have updated READMEs and doc comments. Check by hand |
| `regression-test` | Every fixed bug has a test that fails without the fix |
| `runbook` | A new operational procedure has a runbook |
| `commit-refs` | Commits carry `Refs:` lines, where the project uses them |

## Decision capture

At the end of a session, or when the owner asks, follow [reference/decisions.md](reference/decisions.md). Write nothing until the owner agrees.
