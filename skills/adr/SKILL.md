---
name: adr
description: Defines the content and structure of an Architecture Decision Record. Reference when assembling or reviewing adr/*.md.
---

# ADR

Defines what an Architecture Decision Record contains. An ADR is the human-readable rationale behind an architecture decision; the Stage 5 `[record]` gate criterion — "architecture review approval, bound to artifact version hash" — is satisfied by a **schema-valid Approval record** (`schemas/approval.schema.json`), not by the ADR prose itself. The ADR is why a human signed that approval; the Approval record is the machine-checkable proof that they did (Constitution C2).

## Schema anchor

`schemas/approval.schema.json`. An ADR should reference the specific approval record (by `criterion` and `artifact`) that its decision corresponds to, once that approval exists.

## Standard sections

1. **Title** — a short, specific name for the decision, not "Architecture Decisions for Slice X".
2. **Status** — proposed / accepted / superseded (and by which later ADR, if superseded — never delete an ADR).
3. **Context** — what forces are in tension. Cite the Behaviors, Divergences, or coupling evidence that drove the decision, by ID.
4. **Decision** — the actual choice, stated plainly.
5. **Consequences** — what this makes easier, what it makes harder, and what it forecloses. Include the anticorruption-layer / context-map pattern implications if the decision touches a boundary (`knowledge/ddd-reference.md` §1.3).

## Behavior-ID citation

Cite the Behavior IDs, Divergence IDs, or Context IDs that motivated the decision wherever they are the actual reason — an ADR that asserts a rationale with no traceable evidence is an opinion, not a record.

## What this skill does not cover

Whether the decision was correct — that is what the human architecture reviewer's Approval record attests to (Constitution C2's escape hatch: the gate checks the record exists and is schema-valid, not that the judgment was right).

## Minimal worked example (excerpt)

```markdown
# ADR-0003: Ordering integrates with legacy Billing via an Anticorruption Layer

## Status
Accepted

## Context
BHV-0011, BHV-0057 (DVG-0003) show Billing's OPEN/CLOSED status is invoice
lifecycle, not order lifecycle — a false cognate, not shared vocabulary.

## Decision
Ordering owns its own status model. A translation adapter converts to/from
Billing's model at the boundary; Billing's model never leaks into Ordering.

## Consequences
Adds one translation layer to maintain. Protects Ordering's model from
drift if Billing's status semantics change later.
```
