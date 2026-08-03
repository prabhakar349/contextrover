# Build Constitution — contextrover

Non-negotiable principles governing how this plugin is built. These bind the builder agent. Violating one is a build failure, not a style disagreement.

---

## C1 — The evidence layer is the product

Everything downstream of the specification is ordinary spec-driven development and should defer to existing tooling. The original contribution of this plugin is:

1. Disciplined extraction of behavior from an existing system
2. A traceability spine linking every downstream artifact back to that evidence
3. Verification generated from evidence rather than from intent

Build depth in that order. A shallow Stage 7 command is acceptable. A shallow Stage 1 is not.

## C2 — Every gate must be machine-checkable

A stage gate that requires a human to read a document and form an opinion is not a gate. Every exit criterion in the framework must be expressible as a script that exits 0 or non-zero.

Where a criterion genuinely requires human judgment (boundary decisions, divergence classification), the *gate* is that a signed adjudication record exists — not that the judgment was correct. The record's existence and schema-validity are checkable; its wisdom is not.

## C3 — Read-only by default; declare tools explicitly

Every agent definition must declare its `tools` frontmatter field explicitly. Never omit it and inherit.

Discovery agents get `Read, Grep, Glob` and nothing else. This is what allows them to run unattended in approval-gated environments: a subagent cannot surface a permission prompt, so a tool call matching an `ask` rule is silently **denied**, not queued. An agent that needs approval is an agent that fails.

Any agent needing write or execute access must be invoked from the main session, not spawned as a subagent.

## C4 — Nothing organization-specific ships

The repository is public and domain-agnostic. It must contain no internal standards, platform names, service inventories, topic names, endpoint lists, compliance interpretations, or security baselines.

Organization content lives in a `constitution.md` supplied locally by the adopting team. The repository ships `constitution.template.md` with commented placeholders only.

**`constitution.md` must be in `.gitignore` from the first commit.** A missing constitution must produce a clear, actionable error at Stage 0 — never a silent default. Silent fallbacks are how internal content ends up committed to a public fork.

## C5 — Minimize execution; prefer reading

In approval-gated environments every shell invocation is an approval event, and approval events are the throughput limit — not tokens, not model latency.

- Prefer analysis by reading files over analysis by running scripts.
- Where computation is genuinely required, it goes in one committed script that is reviewed once, never in ad-hoc commands approved every time.
- Scripts use the Python standard library only. No third-party dependencies, no package installs, no network access.
- Every script must be runnable as `python3 scripts/<name>.py` with no setup.

## C6 — Ensembles only where no oracle exists

Multi-pass ensemble extraction costs K× tokens, K× wall-clock and K× approval events. Spend it only where a mechanical check cannot settle the question.

- **Ensemble:** Stage 1 (unknown unknowns), Stage 2 (architectural judgment).
- **Adversarial single-pass:** Stage 5, Stage 6.
- **Never:** Stage 7 onward. The characterization harness is the oracle. Debating what a test can decide is waste.

Consensus measures *agreement*, not correctness. Vary the framing, not just the model — different entry points into a codebase (routes, tests, call sites, logs) buy more independence than different model tiers, and raise no policy questions about model access.

## C7 — Artifacts are data first, documents second

Every artifact is written as schema-valid JSON under the working directory. Human-readable markdown is *generated from* the JSON, never authored alongside it.

Rationale: lint rules, coverage metrics, and orphan detection operate on the JSON. A markdown-first artifact cannot be gated automatically, which violates C2.

## C8 — Language specifics live in packs, nowhere else

Stages 0, 2, 3, 4, 5 and 8 are language-independent and must contain zero language-specific content. **Only Stages 1 (Domain Discovery), 6 (Verification Design) and 7 (Execution) consult a language pack** — discovery patterns, characterization harness conventions, and architecture-fitness tooling respectively.

Characterization operates at the protocol boundary — HTTP and event payloads — never at language internals. Source and target language are independent choices and the framework must never assume they match.

If language-specific logic appears outside `packs/`, it is a defect.

## C9 — No business logic in commands

Commands orchestrate: they select agents, set order, and enforce gates. Skills define what an artifact contains. Agents define how evidence is gathered.

A command containing extraction logic or artifact structure is a defect. This keeps the stages composable and the skills reusable outside the stage drivers.

## C10 — Fail loudly on incomplete evidence

Where the framework cannot establish something — unknown event consumers, unmaskable non-determinism, unreachable code paths — it must record an explicit `unknown` with a reason, never omit it and never guess.

An inventory that silently omits what it could not determine is more dangerous than no inventory, because it will be trusted. Recall matters more than precision here: a false positive costs one review, a false negative is a production incident during cutover.
