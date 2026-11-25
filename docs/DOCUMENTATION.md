# Documentation policy

This document says where each kind of documentation lives in this repository, when it is written, and what "done" means. It is the repository's rule: where it and a tool's defaults disagree, this document wins. It is adapted from the default policy of the `abdullah-docs` skill ([`skills/abdullah-docs/reference/policy-default.md`](../skills/abdullah-docs/reference/policy-default.md)), which this repository uses on itself.

Documentation profile: lean

```abdullah-docs
adr-dir: .agents/adr
base: origin/main
specs: docs/design
plans: docs/plans
history: docs/plans/**, docs/design/**
examples: skills/**, README.md, CLAUDE.md, AGENTS.md, docs/abdullah-docs.md, docs/setup-abdullah-docs.md, .agents/install-block.md, .agents/writing-docs.md
```

The block above holds the settings the documentation checks read: the ADR folder, the base branch, the spec and plan folders, documents that are history, and files whose paths describe other projects. A key left out means the default. The skills' own pages, the README, the agent instructions and the docs pages are examples: their backticked paths describe the projects the skills run in, not this repository.

## The four questions

Every change answers four questions, each in a fixed place:

| Question | Where the answer lives |
|---|---|
| **Why** does this exist, and why was it built this way? | A design, or an ADR |
| **What** changed, and how? | The pull request and its commits |
| **How do we know** it works? | Tests, with a regression test for every bug |
| **When** did it ship, and in which version? | The git tag and `CHANGELOG.md` |

## Rules

1. **Designs are the source of truth.** When code must differ from an approved design, the same change updates the design or adds an ADR.
2. **Decisions are recorded, not remembered.** A decision made in a conversation is written down before the session ends.
3. **Nothing is deleted.** A superseded ADR or design stays, and says what replaced it.
4. **Documentation lives in this repository.** External tools (issue trackers, chat) receive copies only.
5. **English.** Documents are written in English.
6. **Dates and names.** Dates are ISO (`YYYY-MM-DD`). File names are lower-kebab-case.
7. **Code comments explain why, not what.** Public contracts (script options, exit codes, output formats) carry doc comments or `--help` text.
8. **No empty documents.** A document is written when it has content, never as a placeholder.
9. **Nothing private.** No path on a contributor's machine, no private project name and no personal data in any committed file.

## Profile

This repository uses the `lean` profile: the map, the changelog, the ADR folder, the build-and-test instructions and the READMEs always exist; other documents appear when they first have content.

## Where documents live

| Document | Location | Name |
|---|---|---|
| Documentation map | `docs/README.md` | |
| Changelog | `CHANGELOG.md` | [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format |
| ADRs | `.agents/adr/` | `NNNN-<title>.md`, listed in `.agents/adr/README.md` |
| Designs | `docs/design/` | `YYYY-MM-DD-<topic>-design.md` |
| Plans | `docs/plans/` | `YYYY-MM-DD-<topic>.md` |
| Build and test | `CLAUDE.md` and `AGENTS.md`, section "Checks" | |
| README | `README.md` | |
| A page per skill | `docs/` | `<skill-name>.md`, in the template of `.agents/writing-docs.md` |
| Install wording | `.agents/install-block.md` | Copied verbatim into `README.md`, `CLAUDE.md` and `AGENTS.md` |

Designs and plans are history once carried out: they are not updated afterwards, and the checks report their stale paths as warnings. An architecture overview, runbooks and incident records are written when they first have content, in the default places of the skill's policy (an architecture page, a runbooks folder and an incidents folder under `docs/`).

## ADRs

An ADR (architecture decision record) records one decision: its context, the decision, the alternatives, and the consequences.

- **When.** Only when the decision is all three: hard to reverse, surprising without context, and the result of a real trade-off. It may be a single paragraph.
- **Always.** When code deviates from an approved design and the design is not updated instead.
- **Numbers** are one more than the highest number on this branch and on the base branch. Every ADR is listed in the index. Create one with `new_adr.py --root . --policy docs/DOCUMENTATION.md --title "<title>"`.
- **Status** is one of `Proposed`, `Accepted`, `Rejected`, `Deprecated`, `Superseded by NNNN`. An ADR changed by a later one says `amended by NNNN` on its status line.
- **Never deleted.** A replaced ADR is marked superseded and links to its replacement.

## Changelog

`CHANGELOG.md` follows Keep a Changelog. Every user-visible or behavioral change to a skill, a script or an install route adds an entry under `## [Unreleased]`, in one of the subsections `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`. Released sections are not edited. A release moves the unreleased entries into a version section, bumps `version` in `.claude-plugin/plugin.json`, and is tagged `vX.Y.Z`.

## Definition of done

A change is done when each item is true, or does not apply and the pull request says why:

- [ ] A design or ADR records why the change was made, and code matches its design.
- [ ] A user-visible or behavioral change has an entry under `[Unreleased]` in `CHANGELOG.md`.
- [ ] A changed skill has an updated docs page, and `README.md` and `.claude-plugin/plugin.json` list every skill.
- [ ] Every fixed bug has a regression test that fails without the fix.
- [ ] Commits reference the design section, ADR or issue they implement (`Refs:` lines).
- [ ] The checks in `CLAUDE.md` pass: front matter, both test suites, the documentation check, and `claude plugin validate . --strict` after a manifest change.

## Tracing a problem

To find why something behaves as it does:

1. **Symptom to version.** Find the first version with the problem in `CHANGELOG.md` and the git tags (`git tag --contains <commit>`).
2. **Version to commit.** Find the change with `git log`, `git log -S "<text>"` or `git blame` on the lines involved.
3. **Commit to pull request.** Read the pull request and the commit's `Refs:` lines.
4. **Pull request to decision.** Follow the references to the ADR or design section.
5. **Decision to requirement.** The design names the requirement the decision serves.

If a link in that chain is missing, add it when the answer is found.
