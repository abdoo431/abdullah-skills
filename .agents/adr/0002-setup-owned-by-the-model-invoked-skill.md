# 0002. Setup owned by the model-invoked skill

- **Status:** Accepted
- **Date:** 2026-11-25
- **Deciders:** The repository owner
- **Related:** Call C9 and decision D8 of the [design](../../docs/design/2026-11-25-abdullah-docs-design.md#4-decisions); [`skills/abdullah-docs/reference/setup.md`](../../skills/abdullah-docs/reference/setup.md)

## Context

Setup is its own user-invoked skill, `setup-abdullah-docs`, and when `abdullah-docs` runs in a project that has not been set up, it starts the setup itself (D8). `setup-abdullah-docs` carries `disable-model-invocation: true` and `policy.allow_implicit_invocation: false`, so no agent fires it on its own: a documentation policy is written only when someone asks for it, or after the owner agrees to an automatic start.

A user-invoked skill cannot be invoked by another skill in any harness. If the setup procedure lived in `setup-abdullah-docs`, `abdullah-docs` could not reach it, and the automatic start of D8 would not work.

## Decision

The setup procedure lives in the model-invoked skill, in `skills/abdullah-docs/reference/setup.md`. `setup-abdullah-docs` is a thin entry point: it calls the Skill tool with `abdullah-docs` and follows that page. There is one copy of the procedure.

## Alternatives considered

| Option | Pros | Cons |
|--------|------|------|
| The procedure in `setup-abdullah-docs` | The name says where it is | `abdullah-docs` cannot invoke a user-invoked skill, so the automatic start breaks |
| A copy of the procedure in each skill | Each skill stands alone | Two copies drift apart |
| Make `setup-abdullah-docs` model-invoked | `abdullah-docs` could invoke it | Agents could start a setup no one asked for, which D8 rules out |
| One skill, with no separate setup entry point | Nothing to keep in step | No command for the owner to run, or re-run, the setup on request |

## Consequences

- The automatic start and the user's command run the same steps.
- A change to the setup is made in `skills/abdullah-docs/reference/setup.md` only; `setup-abdullah-docs` rarely changes.
- `setup-abdullah-docs` needs `abdullah-docs` installed. They ship in the same plugin, and `setup-abdullah-docs` tells the owner where to install `abdullah-docs` when it is missing.
