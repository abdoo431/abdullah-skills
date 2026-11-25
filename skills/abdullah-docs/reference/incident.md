# Incident records

An incident record explains a bug that escaped: what happened, why, how it was fixed, and what stops it happening again.

## When to write one

Write one when a bug:

- was found in a demo or a release, or
- took more than an hour to diagnose.

In `lean`, the first qualifying bug creates the incident folder. In `full`, the template is in place from setup. Do not write a record for a bug caught in review or by the tests.

## How

1. Use the project's template if it has one (by default `docs/incidents/template.md`). Otherwise use [../templates/incident.md](../templates/incident.md).
2. Save it where the policy says, by default `docs/incidents/YYYY-MM-DD-<summary>.md`, dated the day the bug was found.
3. Fill it from facts: the logs, the commits, the conversation. Write anything you cannot confirm as `> Needs confirmation: <question>`.
4. Add a regression test that fails without the fix, and name it in the record.
5. Link the record from the fix commit (a `Refs:` line, where the project uses them) and from the changelog entry under `### Fixed`.
6. If the fix involved a decision that meets the profile's ADR test, write the ADR too ([adr.md](adr.md)) and link it.
7. Add the incident folder to the documentation map when it is new.

A record is never deleted. If a later finding changes the root cause, add a dated note at the end.
