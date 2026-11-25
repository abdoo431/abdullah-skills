# Decision capture

Decisions made in conversation are lost when the session ends. Decision capture finds them and, with the owner's agreement, writes them where they belong.

## When

- At the end of a session.
- When the owner asks.

## Steps

1. **Review the conversation** for decisions:
   - a choice between options ("use SQLite, not Postgres");
   - a rule the owner set ("never call the payment API from the client");
   - an agreed deviation from a spec or from the project's policy.
2. **Check each one against the record.** Search the specs, the ADRs and the policy. A decision already written there, with the same meaning, needs nothing.
3. **List the unrecorded decisions** for the owner. For each, give:
   - the decision, in one sentence;
   - a proposed home: a spec section (name it), the policy, or a new ADR when it meets the profile's test ([adr.md](adr.md#when-to-write-one));
   - for an ADR, whether it would be short (`lean`) or full.
4. **Wait for the owner.** The owner may accept, change the home, or drop each item.
5. **Write only what the owner accepted.** Create ADRs with `new_adr.py` ([adr.md](adr.md#write-a-new-adr)). Edit specs in every language version the policy requires.
6. **Report** what was written and where.

If there are no unrecorded decisions, say so in one line.
