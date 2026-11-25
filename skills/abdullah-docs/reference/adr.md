# ADRs

An ADR (architecture decision record) records one decision: its context, the decision, the alternatives, and the consequences. Follow the project's policy first; this page fills only what it leaves unsaid.

## When to write one

Read the profile from the policy's `Documentation profile:` line. No line means `lean`.

**`lean`:** write an ADR only when the decision is all three:

1. **Hard to reverse.** Undoing it later costs real work: a data format, a framework, a public interface.
2. **Surprising without context.** A new reader would ask "why was it done this way?"
3. **The result of a real trade-off.** There were other reasonable options, and something was given up.

If one is missing, the decision belongs in a commit message, a code comment or a spec, not an ADR. A `lean` ADR may be one paragraph: use `--short`, unless the project has its own ADR template.

**`full`:** write one for every significant technical decision, as the policy defines it (by default: a framework, a data store, a public interface or protocol, a dependency with lock-in, a deployment or security approach). Use the full template.

**Both profiles:** write one when code must deviate from an approved spec and the spec is not updated instead, and when the owner takes a decision in conversation that meets the profile's test.

## Write a new ADR

1. Run `git fetch` for the base branch's remote, so the number accounts for ADRs merged since this branch started.
2. Run:

   ```
   python <this skill's folder>/scripts/new_adr.py --root <repo> --title "<decision title>" [--short]
   ```

   Add `--policy <policy file>` when the policy is not in a default place. The script:
   - takes the number one above the highest in the ADR folder, both locally and on the base branch;
   - writes `NNNN-<title>.md` with today's date and `Status: Proposed`, from the project's template (`0000-template.md` or `template.md` in the ADR folder) or the skill's full template; `--short` always uses the skill's one-paragraph template;
   - adds a row to the index, in number order;
   - prints only the new file's path. Warnings go to stderr: a `warning: base` line means the number comes from local ADRs only, so say so.
3. If it exits 2, it wrote nothing. Read its message. The causes:
   - **The index is in an unknown shape** (neither a table nor a list of links). Add the row by hand, or propose turning the index into a table.
   - **The ADR folder holds ADR-like files it cannot number** (for example `ADR-007-use-redis.md` or `7_use_redis.md`), common in an adopted layout. Propose renaming them to `NNNN-<title>.md` and rename only with the owner's agreement, or pass `--adr-dir` for the folder that holds the numbered ADRs.
   - **The index is not UTF-8.** Convert it to UTF-8, then run the script again.
   - **The title is empty**, or has no ASCII letter or digit (the file name is built from them).
   - **The policy file named by `--policy` does not exist**, or `--root` is not a directory.
4. Fill every section from facts: the code, the history, the conversation. Write anything you cannot confirm as `> Needs confirmation: <question>`.
5. Link the ADR from where the project uses such links: the related README, the changelog entry, and the commit's `Refs:` line.
6. Change `Proposed` to `Accepted` only when the owner accepts the decision. Update the status in the index too.

## Retroactive ADRs

Setup records the major decisions the code already shows (step 5 of [setup.md](setup.md)). Such an ADR records a decision already in force, not a new one, so it needs no fresh decision by the owner. Its status line reads `Accepted (recorded retroactively on YYYY-MM-DD)`, with the day it was written, and its index status is `Accepted`. Its context comes from the code and the git history only; a reason they do not show is a `Needs confirmation` question.

## Supersede or amend

Never delete an ADR, and never rewrite its decision.

**Supersede** (a later decision replaces it):

1. Write the new ADR as above. In its `Related` field, write `Supersedes [NNNN](NNNN-old-title.md)`.
2. In the old ADR, set the status line to `Superseded by [MMMM](MMMM-new-title.md)`.
3. Set the old ADR's status in the index to match.

**Amend** (a later decision changes part of it):

1. Write the new ADR, and name the ADR it amends in its `Related` field.
2. Add `amended by [MMMM](MMMM-new-title.md)` to the old ADR's status line, for example `Accepted, amended by [0012](0012-cache-in-memory.md)`.

Leave the rest of the old ADR as it was.

## Renumber after a collision

`check_docs.py` reports `adr-number` when this branch's ADR uses a number that the base branch already gave to another ADR. The base's ADR is merged and linked from elsewhere, so this branch's ADR moves:

1. Run `git fetch`, then find the next free number: one above the highest in the ADR folder locally and on the base (`git ls-tree --name-only <base> -- <adr-dir>/`).
2. Rename the file (`git mv`), keeping the number width.
3. Change the number in its title line.
4. Change its row in the index: the number, the link, and the row's place in number order.
5. Change every inbound link: search the repository for the old file name, including other ADRs, READMEs, the changelog and specs.
6. Run `check_docs.py` again.
7. Say in your final message which ADR moved, from which number to which.

## Spec deviation

When code must differ from an approved spec, the same change does one of these:

- Updates the spec, in every language version the project's policy requires.
- Writes an ADR that records the deviation and links to the spec section it departs from.

Prefer the spec update when the spec was simply wrong. Write an ADR when the deviation is a decision someone will later ask about.
