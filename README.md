# abdullah-skills

Agent skills for traceable project documentation and, next, versioning. They follow the [Agent Skills](https://agentskills.io) format, so they work in Claude Code, Codex, GitHub Copilot, Gemini CLI, Cursor, OpenCode and other agents that support it, on any number of projects.

## The problem

A project's documentation rules usually live in that project's own files. They do not travel to the next project, and an agent forgets them in ordinary feature work, when nothing about the task looks like documentation. Two slips of that kind are common:

- **A duplicate ADR number.** A branch takes the next ADR number; while it is open, the main branch gives the same number to another ADR. Nothing fails until someone notices two files named `0026-…`.
- **A changelog entry in a released section.** A merge from the main branch moves the `[Unreleased]` heading, and the branch's entry ends up under a version that has already shipped.

Both are mechanical, and a check that compares the branch with a freshly fetched main branch catches both.

## The fix

`abdullah-docs` gives a project a documentation discipline in which every change answers four questions, each with a fixed home:

| Question | Where the answer lives |
|---|---|
| **Why** does this exist, and why was it built this way? | A spec, or an ADR |
| **What** changed, and how? | The pull request and its commits |
| **How do we know** it works? | Tests, with a regression test for every bug |
| **When** did it ship, and in which version? | The git tag and `CHANGELOG.md` |

With those links in place, a problem can be traced from the symptom to the commit, from the commit to the decision behind it, and from the decision to the requirement.

The skill follows the project's own documentation policy, or a default one when there is none. Its scripts number and index ADRs, check links, code paths, ADR numbers and changelog placement against the main branch, and list what the diff shows for each definition-of-done item. A short section in the project's `CLAUDE.md` or `AGENTS.md` makes every session run the done check before calling a task done, even when the task is not about documentation.

## Step 1: install

Pick one route per agent. Managed installs update themselves; manual installs do not. A route marked untested has not yet been run against the published repository.

### Claude Code (managed, tested 2026-11-25 with Claude Code 2.1.330)

```
claude plugin marketplace add abdoo431/abdullah-skills
claude plugin install abdullah-skills@abdullah
```

### Codex (managed, tested 2026-11-25 with Codex CLI 0.172.0)

```
codex plugin marketplace add abdoo431/abdullah-skills
codex plugin add abdullah-skills@abdullah
```

Codex updates the plugin at startup. The `codex plugin` command needs a recent Codex CLI; 0.121.0 does not have it.

### GitHub Copilot CLI and VS Code (managed, untested)

```
copilot plugin marketplace add abdoo431/abdullah-skills
copilot plugin install abdullah-skills@abdullah
```

VS Code uses the same marketplace. Updates need a one-time opt-in.

### Gemini CLI (manual, untested)

```
gemini skills install https://github.com/abdoo431/abdullah-skills.git --path skills
```

This copy does not update itself.

### Any other agent (manual, tested 2026-11-25 with Claude Code as the agent)

```
npx skills@latest add abdoo431/abdullah-skills
```

It asks which agents and skills to install. To answer up front, name them: `npx skills@latest add abdoo431/abdullah-skills -g -a claude-code -s '*' -y` installs both skills for Claude Code at user level.

This copy does not update itself. Update it with `npx skills@latest update`.

### After installing

Run `/setup-abdullah-docs` once in each project (`/abdullah-skills:setup-abdullah-docs` when installed as a plugin), or let `abdullah-docs` start the setup the first time it runs in a project without a documentation policy.

## Step 2: set up each project

In each project, run `/setup-abdullah-docs` (`/abdullah-skills:setup-abdullah-docs` when installed as a plugin). The setup surveys the project read-only, asks you to choose the `lean` or `full` profile, and shows you drafts of the documentation policy, the documentation map and the section for the agent instructions. It writes nothing until you agree, and it writes a question in place of any fact the code and history do not show.

You can also skip this step: the first time `abdullah-docs` runs in a project without a documentation policy, it offers the same setup on its own.

## Skills

### User-invoked

You run these yourself; no agent starts them on its own.

- [setup-abdullah-docs](skills/setup-abdullah-docs/SKILL.md): set up a project for `abdullah-docs`, or refresh an earlier setup. [How it works](docs/setup-abdullah-docs.md).

### Model-invoked

The agent reaches for these when the task calls for them; you can also invoke them by name.

- [abdullah-docs](skills/abdullah-docs/SKILL.md): keep a project's ADRs, changelog, specs, runbooks, incident records and READMEs traceable, run the done check before a task is called done, and capture decisions made in conversation. [How it works](docs/abdullah-docs.md).

## More

- [Documentation map](docs/README.md): every document in this repository.
- [Changelog](CHANGELOG.md).
- [Reporting a problem](CONTRIBUTING.md).
- License: [MIT](LICENSE).
