# abdullah-docs

Keeps a project's documentation traceable while the agent does ordinary work. Source: [`skills/abdullah-docs/SKILL.md`](../skills/abdullah-docs/SKILL.md).

## What it does

It makes every change answer four questions, each in a fixed place: why it exists (a spec or an ADR), what changed (the pull request and its commits), how we know it works (tests), and when it shipped (the git tag and `CHANGELOG.md`). It writes ADRs, changelog entries, incident records, runbooks and READMEs when a task calls for them, checks the documentation before a task is called done, and captures decisions made in conversation.

The fact that sets it apart: **the project's written policy wins.** The skill brings a default policy, but where the project's `docs/DOCUMENTATION.md` (or equivalent) says something else, the skill follows the project. It may propose a change to a project rule; it never applies one on its own.

## When to reach for it

You rarely need to. It is model-invoked: the agent loads it when it writes or changes documentation, when a decision is made, before a pull request, and before calling a task done. You can also invoke it by name.

The section that setup adds to `CLAUDE.md` or `AGENTS.md` tells every session to run its done check, so the check happens even during feature work that does not look like documentation.

It does not write design specs or implementation plans; spec-writing skills do that. It fixes where those documents live and checks that code still matches them. It does not cut releases or choose version numbers; that is the job of `abdullah-versioning`, still to come.

## Prerequisites

- Git, for the checks against the main branch. Without it, or without a fetched main branch, the scripts check local files only and say so.
- Python 3.10 or later, for the scripts. Without Python, the agent does the same steps by hand and says the scripts did not run.

## Step 0 and the setup

Every task starts by asking whether the project is set up: is there a documentation policy, and the `## Documentation (abdullah-docs)` section in `CLAUDE.md` or `AGENTS.md`? When there is no policy, the skill starts the setup on its own: it tells you, surveys the project, and shows drafts. It writes nothing until you agree. If you decline, it carries on with the default `lean` rules and does not ask again in that session. The setup itself is described in [setup-abdullah-docs](setup-abdullah-docs.md).

## The done check

At the end of any task that touched code or docs, and before a pull request, the agent fetches the main branch and runs `check_docs.py`. It reports, one finding per line:

- an ADR number already taken on the main branch, which the agent fixes by renumbering this branch's ADR;
- an ADR missing from the index, or without a status or date;
- a relative link or a backticked repository path that points to a missing file;
- a changelog line added outside `[Unreleased]`;
- a missing translation, for projects whose policy requires one;
- a missing agent-instructions section.

Then `pr_checklist.py` lists what the diff shows for each definition-of-done item, and the agent reports each item as done, not needed (with the reason), or missing.

## Profiles

A project chooses `lean` or `full` at setup, and the policy records it as a line, `Documentation profile: lean`.

- **`lean`** (the default) keeps the map, the changelog, the ADR folder, a build-run-test runbook and READMEs. Other documents appear when they first have content. An ADR is written only for a decision that is hard to reverse, surprising without context, and the result of a real trade-off, and it may be one paragraph.
- **`full`** also sets up templates for incidents and runbooks and the spec and plan folders, and asks for an ADR for every significant technical decision.

Neither profile creates an empty document to complete a set.

## It's working if

- The agent's final message on a task that touched code or docs lists each definition-of-done item with its status.
- New ADRs get the next free number on the main branch and a row in the ADR index, without you choosing the number.
- Changelog entries land under `[Unreleased]`, in the right subsection.
- At the end of a session, the agent lists decisions from the conversation that no spec or ADR records yet, and writes them only after you agree.
- `check_docs.py --all` exits 0 on your project.

## Where it fits

`abdullah-docs` owns the daily discipline and the setup procedure; [setup-abdullah-docs](setup-abdullah-docs.md) is the command you run to start that procedure yourself. Spec-writing skills write specs and plans, a glossary skill owns a project's glossary, and `abdullah-versioning` will own releases and tags. They meet at `CHANGELOG.md`: this skill writes the `[Unreleased]` entries, and versioning moves them into a release.
