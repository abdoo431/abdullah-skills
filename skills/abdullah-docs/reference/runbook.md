# Runbooks

A runbook is a step-by-step procedure someone can follow without asking: build the project, deploy it, restore a backup, rotate a secret, cut a release.

## When to write one

- **Always:** one for building, running and testing the project. Setup writes it from the scripts and build files that exist.
- **When a new operational procedure appears:** a deploy step, a migration, a recovery, a manual release step. In `lean`, the first such procedure creates the runbook. In `full`, the template is in place from setup.
- **When a procedure changes:** update its runbook in the same change.

## How

1. Use the project's template if it has one (by default `docs/runbooks/template.md`). Otherwise use [../templates/runbook.md](../templates/runbook.md).
2. Save it where the policy says, by default `docs/runbooks/<procedure>.md`, for example `docs/runbooks/restore-database.md`.
3. Write only commands that exist in the project: its scripts, its build files, its CI configuration. Copy them exactly.
4. Say how to check that each important step worked, and what to do when it fails.
5. Write anything you cannot confirm as `> Needs confirmation: <question>`. Never guess a command, a host name or a credential location.
6. Never write a secret into a runbook. Name where it is kept.
7. Add the runbook to the documentation map.
