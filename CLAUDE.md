# abdullah-skills

Rules for maintaining this repository of agent skills. `CLAUDE.md` and `AGENTS.md` are identical: change both in the same commit (a test checks that they match byte for byte).

## Layout

```
README.md                       the problem the skills fix, installation, the skill list by invocation
LICENSE                         MIT
CHANGELOG.md                    Keep a Changelog
CONTRIBUTING.md                 how to report a problem
CLAUDE.md, AGENTS.md            identical: this file
.agents/install-block.md        the one wording of the install commands
.agents/writing-docs.md         the template for the pages in docs/
.agents/adr/                    this repository's own decisions
.claude-plugin/plugin.json      name, version, and the skills array
.claude-plugin/marketplace.json this repository as its own marketplace, named abdullah
.github/workflows/check.yml     the checks below, on Linux and Windows, Python 3.10 and 3.12
docs/DOCUMENTATION.md           this repository's documentation policy
docs/README.md                  the map of this repository's documents
docs/<skill>.md                 the human-facing page for each skill
docs/design/, docs/plans/       designs and implementation plans (history once carried out)
scripts/check_frontmatter.py    every SKILL.md parses and has name and description
scripts/link_skills.py          maintainer only: link the working copy into local agent skill folders
tests/                          repository tests
skills/<skill>/                 one folder per skill: SKILL.md, agents/openai.yaml, and its own files
```

## Skills

| Skill | Invocation | Folder |
|---|---|---|
| `abdullah-docs` | Model-invoked | `skills/abdullah-docs/` |
| `setup-abdullah-docs` | User-invoked only (`disable-model-invocation: true`, `policy.allow_implicit_invocation: false`) | `skills/setup-abdullah-docs/` |
| `abdullah-versioning` | Model-invoked | `skills/abdullah-versioning/` |
| `setup-abdullah-versioning` | User-invoked only (`disable-model-invocation: true`, `policy.allow_implicit_invocation: false`) | `skills/setup-abdullah-versioning/` |

Every skill is listed in `README.md`, under its invocation and linked to its `SKILL.md`, and in the `skills` array of `.claude-plugin/plugin.json`. A new skill also gets a page in `docs/`, written from `.agents/writing-docs.md`, a row in `docs/README.md`, and an `Added` entry in `CHANGELOG.md`. The repository tests check the README and `plugin.json` against the folders under `skills/`.

Rules for skill text:

- `SKILL.md` front matter: `name` equals the folder name; `description` is a non-empty string; quote any value containing `: `.
- Procedure text names no tool of one agent. A dependency on another skill reads: call the Skill tool with `<name>`.
- Skills are real folders: no symbolic links in the repository, because plugin installers drop them.
- Scripts use Python 3.10 or later and the standard library only, and run from any current folder.
- No paths on a contributor's machine, private project names or personal data in any committed file.

## Install wording

The install commands are worded once, in `.agents/install-block.md`. Change them there, then copy the file verbatim into `README.md` (under "Step 1: install") and into this section of both `CLAUDE.md` and `AGENTS.md`; a repository test checks every copy. Mark a route tested only after it has been run against the published repository.

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

It asks which agents and skills to install. To answer up front, name them: `npx skills@latest add abdoo431/abdullah-skills -g -a claude-code -s '*' -y` installs every skill for Claude Code at user level.

This copy does not update itself. Update it with `npx skills@latest update`.

### After installing

Run `/setup-abdullah-docs` once in each project (`/abdullah-skills:setup-abdullah-docs` when installed as a plugin), or let `abdullah-docs` start the setup the first time it runs in a project without a documentation policy.

For releases, run `/setup-abdullah-versioning` once in each project (`/abdullah-skills:setup-abdullah-versioning` when installed as a plugin), or let `abdullah-versioning` start its setup the first time it runs in a project without a release policy.

## Checks

Run these from the repository root before opening a pull request. CI runs the same.

```
python scripts/check_frontmatter.py --root .
python -m unittest discover -s skills/abdullah-docs/tests -t skills/abdullah-docs -v
python -m unittest discover -s skills/abdullah-versioning/tests -t skills/abdullah-versioning -v
python -m unittest discover -s tests -v
python skills/abdullah-docs/scripts/check_docs.py --root . --all --policy docs/DOCUMENTATION.md
```

`check_docs.py --all` checks tracked and untracked files, except those `.gitignore` ignores. Without a fetched `origin/main` it prints one `warning: base` finding; that is expected.

After touching `.claude-plugin/plugin.json` or `.claude-plugin/marketplace.json`, also run:

```
claude plugin validate .claude-plugin/marketplace.json --strict
claude plugin validate .
```

The first must pass. The second must pass, and its only warning must be this one, about the maintainer instructions you are reading:

> CLAUDE.md at the plugin root is not loaded as project context.

The separate "plugin directory checks" that follow also print an `ICON_MISSING` warning, which does not change the result. Any other warning is a problem to fix. `claude plugin validate . --strict` fails on the CLAUDE.md warning by design: see [ADR 0003](.agents/adr/0003-plugin-validation-without-strict-mode-at-the-repository-root.md).

## Releases

- Bump `version` in `.claude-plugin/plugin.json` for every release: plugin installs update only when it changes. It is the repository's only version.
- Move the `[Unreleased]` entries in `CHANGELOG.md` into a section `## [X.Y.Z] - YYYY-MM-DD` with the same version. A repository test checks that the two agree.
- Tag the release `vX.Y.Z`.

## Trying the working copy in your agents

`python scripts/link_skills.py` links each `skills/<skill>` folder into `~/.claude/skills` and `~/.agents/skills` (a junction on Windows, a symbolic link elsewhere), so local agents load the working copy. Pass `--dest <folder>` to choose other folders, `--dry-run` to see what it would do, and `--remove` to remove the links. It replaces its own links but never a real folder.

If the plugin is also installed, disable it before linking (`claude plugin disable abdullah-skills@abdullah` in Claude Code, and the same in any other agent that has it), and enable it again after `--remove`. Otherwise the agent loads both copies, `abdullah-skills:abdullah-docs` from the plugin and `abdullah-docs` from the link, and may run the published one instead of the working copy.

## Documentation (abdullah-docs)

This project follows the policy in docs/DOCUMENTATION.md, using the abdullah-docs skill
(https://github.com/abdoo431/abdullah-skills).
- Before calling any task done, and before opening a pull request, run its done check.
- At the end of a session, run its decision capture.
- If your agent cannot load skills, install them from the link above.
