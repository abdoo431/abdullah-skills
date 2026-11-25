# Writing a docs page

Every skill has one human-facing page in `docs/`, named after the skill (`docs/<skill-name>.md`). The page is for a person deciding whether to use the skill and checking that it works; the agent reads `SKILL.md`, not this page.

Write the sections in this order. Leave out a section marked optional when it would be empty; never write a placeholder.

```markdown
# <skill-name>

<One sentence: what the skill is for.> Source: [`skills/<skill-name>/SKILL.md`](../skills/<skill-name>/SKILL.md).

## What it does

The job, in a short paragraph. Then the one fact that makes the skill behave
differently from the obvious default, stated plainly.

## When to reach for it

Who invokes it: the user (a slash command) or the agent (its description).
Where it ends and a neighbouring skill begins.

## Prerequisites

Optional: only when there are any (a tool, a file, another skill).

## <Section in the skill's own vocabulary>

One to three such sections, named with the words the skill itself uses
(for example "The done check", "Profiles"). Each explains one idea a user meets.

## Common questions

Optional: real questions only, asked by real users or found in issues.
Sized to the evidence: leave the section out until a real question exists.

## It's working if

Signals a reader can check without opening SKILL.md: files that appear,
lines in the agent's final message, a command that exits 0.

## Where it fits

How it relates to the other skills in this repository and to skills elsewhere.
```

Rules:

- Use the skill's own words for its concepts, so a reader can search `SKILL.md` for them.
- Name the slash command both ways: `/<skill-name>`, or `/abdullah-skills:<skill-name>` when installed as a plugin.
- Link to the skill's `SKILL.md` and reference pages rather than repeating their procedures.
- Link a new page from `README.md` and from `docs/README.md`.
