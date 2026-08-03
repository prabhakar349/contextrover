# Language Pack Interface

A Language Pack is where all language-specific content lives (Constitution C8). Only Stage 1 (Domain Discovery), Stage 6 (Verification Design), and Stage 7 (Execution) ever consult a pack. Every other stage is language-independent and must contain zero language-specific content — if you find language-specific logic outside `packs/`, it is a defect.

Discovery agents never hard-code extraction patterns in their own prompts (seam S3.2). They read this interface's sections from the pack for whichever language applies, at runtime.

A pack is a directory `packs/<language>/` containing `PACK.md` (this interface, filled in) and `fitness.json` (machine-readable arch-fitness rules, contract below).

---

## Required frontmatter-equivalent: `discovery_method`

Every `PACK.md` must declare, near the top:

```
discovery_method: pattern
```

`pattern` is the only legal value in v1 — pattern-based (grep/glob) discovery. `lsp` is reserved for a future Language Server Protocol discovery path (seam S3.1, `12-extension-seams.md` §3) and must not be used yet. Discovery agents receive their extraction strategy from this field and this document, never inline — this is what lets LSP be added later as a pack-level change with no change to any agent.

---

## Required sections (REQ-52)

Every `PACK.md` must implement all six of the following, in this order.

### 1. Sync route discovery

Where synchronous endpoints (HTTP, gRPC) are conventionally declared in this language's common frameworks, and what a discovery agent should look for to find them, their methods, paths, and request/response shapes. Read by `agents/sync-surface-extractor.md`.

### 2. Async binding discovery

Where asynchronous bindings (topic publishers, consumers, queue subscriptions) are conventionally declared, and how to recognize partition keys, consumer groups, and delivery-semantics configuration in this ecosystem. Read by `agents/async-surface-extractor.md`.

### 3. Behavior-extraction hints

Where business logic conventionally lives in this ecosystem (vs. framework boilerplate), common idioms for validation and error-mapping, and anything else that helps distinguish a real Behavior from incidental plumbing. Read by `agents/behavior-extractor.md`, and useful background for `agents/divergence-detector.md` and `agents/redaction-policy-assessor.md`.

### 4. Arch-fitness tooling

Names the concrete tool this pack delegates to (`scripts/run-fitness.py` shells out to it; it is never reimplemented — Constitution C5, T09). Must include a `fitness.json` manifest alongside `PACK.md`:

```json
{
  "language": "<language>",
  "rules": [
    { "id": "<rule-id>", "description": "<what it checks>", "command": "<shell command, split with shlex>" }
  ]
}
```

Each rule's `command` runs as a subprocess with cwd set to the target repository root; exit code 0 is a pass. At minimum, every pack's fitness rules must include a check for **no domain logic in adapter packages** and **no adapter types in domain packages** (the Stage 7 gate's specific concern, `07-stages.md`).

### 5. Characterization harness conventions

How this ecosystem's test runner is invoked, how to structure a characterization test so it operates at the protocol boundary (never at language internals — DR1), and any language-specific conventions for masking volatile fields before comparison.

### 6. Build/CI integration

How to run this ecosystem's linter, tests, and build as part of Stage 6/7 gates — the standard commands a CI pipeline in this language would already run, so this framework rides existing tooling rather than inventing new pipeline steps.

---

## What a pack must never do

- Contain organization-specific content (Constitution C4) — frameworks and conventions only, never a specific company's service names or endpoints.
- Duplicate content that belongs in a skill or schema — a pack describes *how to find things in this language*, not *what an artifact must contain* (that split is Constitution C9: agents define how evidence is gathered, skills define what an artifact contains).
