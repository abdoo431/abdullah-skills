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
