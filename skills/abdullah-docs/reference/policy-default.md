# Documentation policy

This document says where each kind of documentation lives in this project, when it is written, and what "done" means. It is the project's rule: where it and a tool's defaults disagree, this document wins.

Documentation profile: lean

```abdullah-docs
adr-dir:
changelog:
base:
history:
pairs:
examples:
```

The block above holds the settings the documentation checks read: the ADR folder, the changelog file, the base branch, documents that are history, language pairs, and files whose paths describe other projects. An empty value means the default.

## The four questions

Every change answers four questions, each in a fixed place:

| Question | Where the answer lives |
|---|---|
| **Why** does this exist, and why was it built this way? | A spec, or an ADR |
| **What** changed, and how? | The pull request and its commits |
| **How do we know** it works? | Tests, with a regression test for every bug |
| **When** did it ship, and in which version? | The git tag and `CHANGELOG.md` |

## Rules

1. **Specs are the source of truth.** When code must differ from an approved spec, the same change updates the spec or adds an ADR.
2. **Decisions are recorded, not remembered.** A decision made in a conversation is written down before the session ends.
3. **Nothing is deleted.** A superseded ADR or spec stays, and says what replaced it.
4. **Documentation lives in this repository.** External tools (wikis, issue trackers, chat) receive copies only.
5. **English.** Documents are written in English.
6. **Dates and names.** Dates are ISO (`YYYY-MM-DD`). File names are lower-kebab-case.
7. **Code comments explain why, not what.** Public contracts (exported functions, APIs, configuration) carry doc comments.
8. **Generated references are never handwritten.** API and schema references are generated from their source; this policy only records that they are.
9. **No empty documents.** A document is written when it has content, never as a placeholder.

## Profiles

This project uses the profile named on the `Documentation profile:` line above.

| Document | `lean` | `full` |
|---|---|---|
| Documentation map `docs/README.md` | Always | Always |
| `CHANGELOG.md` | Always | Always |
| ADRs `docs/adr/` with index and template | Always; ADRs only by the three-part test | Always; ADRs by the broader trigger, full template |
| Runbook: build, run, test | Always | Always |
| README per project or package | Always | Always |
| Architecture overview | When there is more than one component | At setup |
| Specs and plans | When the first major feature is designed | Folders and naming set at setup |
| Incident records | At the first qualifying bug | Template at setup |
| Other runbooks | At the first such procedure | Template at setup |

`full` sets up every type at the start, but still writes no document without content: it creates templates and index files, not empty documents.

## Where documents live

| Document | Location | Name |
|---|---|---|
| Documentation map | `docs/README.md` | |
| Changelog | `CHANGELOG.md` | [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format |
| ADRs | `docs/adr/` | `NNNN-<title>.md`, listed in `docs/adr/README.md` |
| Specs | `docs/superpowers/specs/` | `YYYY-MM-DD-<topic>-design.md` |
| Plans | `docs/superpowers/plans/` | `YYYY-MM-DD-<topic>.md` |
| Architecture overview | `docs/architecture.md` | |
| Runbooks | `docs/runbooks/` | `<procedure>.md` |
| Incident records | `docs/incidents/` | `YYYY-MM-DD-<summary>.md` |
| READMEs | The root of each project or package | `README.md` |

Specs and plans follow the spec-writing tool the project uses. Plans are history once carried out: they are not updated afterwards.

## ADRs

An ADR (architecture decision record) records one decision: its context, the decision, the alternatives, and the consequences.

- **When, in `lean`.** Only when the decision is all three: hard to reverse, surprising without context, and the result of a real trade-off. It may be a single paragraph.
- **When, in `full`.** For every significant technical decision: a framework, a data store, a public interface or protocol, a dependency with lock-in, a deployment or security approach. Uses the full template.
- **Always.** When code deviates from an approved spec and the spec is not updated instead.
- **Numbers** are one more than the highest number on this branch and on the base branch. Every ADR is listed in the index.
- **Status** is one of `Proposed`, `Accepted`, `Rejected`, `Deprecated`, `Superseded by NNNN`. An ADR changed by a later one says `amended by NNNN` on its status line.
- **Never deleted.** A replaced ADR is marked superseded and links to its replacement.

## Changelog

`CHANGELOG.md` follows Keep a Changelog. Every user-visible or behavioral change adds an entry under `## [Unreleased]`, in one of the subsections `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`. Released sections are not edited. A release moves the unreleased entries into a version section.

## Incidents, runbooks and READMEs

- **Incident record:** for a bug found in a demo or a release, or one that took more than an hour to diagnose. It links to the fix commit, and the changelog entry links to it.
- **Runbook:** for every operational procedure (deploying, restoring, rotating a secret, releasing), and always one for building, running and testing.
- **README:** for every project or package, updated when its public interface changes.

## Definition of done

A change is done when each item is true, or does not apply and the pull request says why:

- [ ] A spec or ADR records why the change was made, and code matches its spec.
- [ ] A user-visible or behavioral change has an entry under `[Unreleased]` in `CHANGELOG.md`.
- [ ] Changed public interfaces have updated READMEs and doc comments.
- [ ] Every fixed bug has a regression test that fails without the fix.
- [ ] A new operational procedure has a runbook.
- [ ] Commits reference the spec, ADR or issue they implement (`Refs:` lines), where the project uses them.
- [ ] The documentation check passes: links, paths, ADR numbers and index, changelog placement.

## Tracing a problem

To find why something behaves as it does:

1. **Symptom to version.** Find the first version with the problem in `CHANGELOG.md` and the git tags (`git tag --contains <commit>`).
2. **Version to commit.** Find the change with `git log`, `git log -S "<text>"` or `git blame` on the lines involved.
3. **Commit to pull request.** Read the pull request and the commit's `Refs:` lines.
4. **Pull request to decision.** Follow the references to the ADR or spec section.
5. **Decision to requirement.** The spec names the requirement the decision serves.

If a link in that chain is missing, add it when the answer is found.
