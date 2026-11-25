# Contributing

## Reporting a problem

Open an issue on [GitHub](https://github.com/abdoo431/abdullah-skills/issues) with three things:

1. **What you ran.** The agent and its version, how you installed the skills (the route from the [README](README.md#step-1-install)), the plugin version from `.claude-plugin/plugin.json` or the release you installed, and the request or command you gave, for example `/setup-abdullah-docs` or "add an ADR for the cache".
2. **What the skill did.** The agent's reply, the files it wrote or changed, and any script output, such as the findings of `check_docs.py`.
3. **What you expected.** What should have happened instead, and why: a rule in your project's documentation policy, a line in the skill's `SKILL.md`, or what the docs page promises.

Leave out anything private: paths on your machine, private project names, secrets. A small sample repository that shows the problem helps most.

## Changing the repository

Read [`CLAUDE.md`](CLAUDE.md) first: it lists the layout, the checks to run before a pull request, and how a release is made. The documentation rules are in [`docs/DOCUMENTATION.md`](docs/DOCUMENTATION.md).
