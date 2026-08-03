---
name: contract-tests
description: Defines the content and structure of consumer-driven contract tests for a Slice's interfaces. Reference when assembling or reviewing slices/<id>/verification/contracts/*.
---

# Contract Tests

Defines what a contract test must assert. Distinct from the characterization suite: characterization proves the *new* implementation matches the *old* system's observed behavior; contract tests prove the new implementation's published surface still satisfies what its actual consumers depend on, independent of internal changes.

## Schema anchor

`schemas/interface.schema.json`. Each contract test corresponds to exactly one Interface record and should be named or tagged with that Interface's `id` — the traceability spine runs Interface → contract test just as it runs Behavior → characterization test.

## Content obligations

- One contract test set per Interface with known consumers (`interface.consumers[]` non-empty, or `consumers_complete: false` — an interface with possibly-unknown consumers still needs its declared contract tested).
- For **sync** interfaces: assert the request/response schema consumers actually rely on, not the full internal schema if it is broader than what is published.
- For **async** interfaces: assert payload schema, and where ordering or partition key are part of the published contract, assert those too — a consumer relying on partition-key-based ordering breaks silently if that contract is dropped, with no error anywhere.
- Where `consumers[]` entries have low or unknown confidence, treat the contract conservatively — do not narrow it based on unconfirmed consumer assumptions.

## Behavior-ID citation

Contract tests cite the Interface, not a Behavior directly, but should reference the Behaviors whose evidence established the contract's shape (`behavior.interfaces[]` pointing at this Interface) so a reviewer can trace why the contract looks the way it does.

## What this skill does not cover

Consumer migration guidance or deprecation notices for the legacy surface — that is the Consumer Migration Workstream's territory (`07-stages.md` §4), driven by `/rover-migrate`, not this skill.
