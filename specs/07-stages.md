# Stage Model — SINGLE SOURCE OF TRUTH

Replaces the former `07-phases.md` and `10-journey.md`, now superseded stubs. There is one stage model and it is this one. Nothing in the pack uses "Phase".

Scope is **v1: brownfield only** (Characterization oracle). Greenfield is a reserved extension — see `12-extension-seams.md`. Terminology per `09-glossary.md`.

---

## 1. The nine stages

| # | Stage | Scope | Mode | Approver |
|---|---|---|---|---|
| 0 | Engagement Intake | Engagement | Conversational, human-led | Program lead |
| 1 | Domain Discovery | Engagement | Unattended, Consensus Run | Tech lead |
| 2 | Strategic Design | Engagement | Human-led, agent-prepared | Boundary approver (**human**) |
| 3 | Solution Outline | Per Slice | Agent-drafted, reviewed | Product + tech lead |
| 4 | Delivery Roadmap | Engagement | Agent-drafted, human-shaped | **Leadership** |
| 5 | Tactical Design | Per Slice, JIT | Human-led, agent-prepared | Architecture review |
| 6 | Verification Design | Per Slice | Adversarial, agent-heavy | QA / SRE |
| 7 | Execution | Per Slice | Dispatched, harness-gated | Code review |
| 8 | Transition | **Per Modeled Context** | Human-gated | Change management + sunset authority |

Stages 0–2 and 4 are Engagement-level and run once. Stages 3, 5, 6, 7 repeat per Slice. Stage 8 runs per Modeled Context, once all its Slices reach `Accepted`.

```
0 ─ 1 ─ 2 ─ 3 ─ 4 ─┬─ [ 5 ─ 6 ─ 7 ] per Slice ─→ Slice Accepted
                   │
                   └─ Consumer Migration Workstream (parallel, never blocking)
                              ↓
        all Slices in a Context Accepted ─→ 8 Transition (that Context)
```

**Why Transition is per Context, not per Slice.** You cannot canary one Slice of a Context whose sibling Slices are not built — the Context is the deployable boundary. A Slice's terminal state is `Accepted`; production exposure belongs to the Context's cutover plan.

**Why Verification Design (6) is its own stage.** The harness must exist before the code it judges, and the Redaction Policy GO/NO-GO decision must be a gate between design and build. It is a separate stage from Tactical Design for that reason alone.

---

## 2. The harness freeze

At the Stage 6 gate, the characterization suite for a Slice is hashed and the hash recorded in `slices/<id>/harness.lock`. Stage 7 verifies against the locked hash.

If the harness changes during Stage 7, the Stage 6 gate is void and must be re-approved by the QA/SRE approver with a recorded rationale.

This is the mechanism behind the claim *"the target moved, the scoreboard didn't."* Without the lock the claim is unenforced and an implementer can quietly relax failing tests. **It is not optional.**

---

## 3. Stage contracts

Notation: **Gate** lists criteria and, in brackets, which script checks it. Criteria marked **[record]** are not machine-decidable and use the Build Constitution C2 escape hatch — the gate checks that a schema-valid signed approval record exists, not that the judgment was correct.

### Stage 0 — Engagement Intake

- **Command** `/rover-init`
- **Inputs** operator knowledge; `charter.template.md`
- **Activities** six-section intake interview (`06-intake.md`, sections A–F); Access Probe per connector; Engagement Charter completion; derived risk computation; `git init` in `.contextrover/`
- **Outputs** `intake.json`, `charter.md` (gitignored), `state.json`, initial commit
- **Gate** intake schema-valid [`validate-artifacts.py --stage 0`]; charter present and contains no placeholder tokens [same]; every high risk resolved or explicitly accepted [same]
- **Failure modes** proceeding on a placeholder charter; collecting connector config for unreachable systems; accepting a mandated service count without reframing the success metric

### Stage 1 — Domain Discovery

- **Command** `/rover-discover`
- **Mode** unattended. K read-only passes, zero approval events.
- **Agents** sync-surface-extractor, async-surface-extractor, behavior-extractor, dependency-mapper, consumer-mapper, call-sequence-analyst, change-coupling-analyst, divergence-detector, redaction-policy-assessor. **Consensus aggregation runs in the main session, not as a subagent** (T11)
- **Outputs** `inventory/{interfaces,behaviors,divergences,coupling,sequences,redaction-policy}.json`, `retirement.json` (v0), `consensus/*.json`, `passes/1/<k>/` retained
- **Gate** every artifact schema-valid [`validate-artifacts.py --stage 1`]; every Behavior has an ID and ≥1 evidence entry [`trace-lint.py --stage 1`]; every async Interface has consumer evidence or explicit `consumers_complete:false` [same]; agreement rate computed and recorded [same]; found-by-one list reviewed **[record]**
- **Note** a Redaction Policy NO-GO does **not** block this stage. It blocks Stage 6 (see REQ-05 correction in `01-spec.md`).

### Stage 2 — Strategic Design

- **Command** `/rover-model`
- **Mode** human-led. K competing boundary proposals **plus the operator's own hypothesis** as an equal candidate.
- **Agents** boundary-proposer (×K). **Consensus aggregation and adjudication-record writing run in the main session** — an Adjudication requires a human decider, and a subagent cannot surface an approval prompt
- **Outputs** `model/contexts.json`, `model/context-map.json`, `model/variation-policy.json`, `adjudications/*.json` (human decider), `divergences.json` updated with classifications
- **Gate** every Behavior maps to exactly one Modeled Context [`trace-lint.py --stage 2`]; zero `unclassified` Divergences [same]; every Modeled Context owns ≥1 aggregate root [same]; **[record]** signed Adjudication exists per boundary decision and per Divergence classification, each naming a human decider
- **Failure modes** letting an agent decide boundaries; arriving at slightly fewer nanoservices and declaring victory; reconciling Divergences instead of classifying them

### Stage 3 — Solution Outline

- **Command** `/rover-outline`
- **Inputs** approved contexts; Behaviors mapped to contexts
- **Activities** partition Behaviors into Slices; draft PRD and acceptance criteria per Slice; test approach; size in Behaviors and Interfaces
- **Outputs** `slices/<id>/{prd.md,acceptance-criteria.json,test-approach.md,size.json}`, `workstreams.json`
- **Gate** every Behavior assigned to exactly one Slice [`trace-lint.py --stage 3`]; every Slice has acceptance criteria and a `size.json` [same]; no Slice exceeds the configured maximum size — oversized Slices must be split before roadmapping [same]; `oracle_strategy` present and equal to `characterization` for all Slices in v1 [same]
- **Note** `size.json` contains **no dates**. Dates are produced only in Stage 4.

### Stage 4 — Delivery Roadmap

- **Command** `/rover-roadmap`
- **Inputs** all `size.json`; Delivery Capacity (`intake.json` §F); business priority supplied by leadership
- **Outputs** `roadmap.json`, rendered roadmap section in the HTML report
- **Rules**
  - **Increment 0 is always the Walking Skeleton** — infrastructure, data stores, pipeline, observability, monitoring, security controls, exercised end to end with minimal functionality. Nothing may precede it.
  - Business priority determines order thereafter. The tool sequences by dependency and blast radius, then defers to stated business order, **flagging conflicts rather than overriding them**.
  - Confidence bands derive from the Stage 1 agreement rate (`11-estimation.md` §5).
  - Re-forecast is mandatory after Increment 0 completes.
- **Gate** every Slice appears exactly once [`trace-lint.py --stage 4`]; Increment 0 is the Walking Skeleton [same]; every Increment has a named owner [same]; capacity model present with the binding constraint named [same]; **[record]** leadership approval bound to the roadmap's version hash

### Stage 5 — Tactical Design (per Slice, just-in-time)

- **Command** `/rover-design <slice-id>`
- **Activities** aggregates with roots and **invariants**, entities, value objects, domain events (past tense), commands (imperative), policies; detailed design doc; API and event contracts for this Slice; legacy adapter specs; inter-service contracts
- **Outputs** `slices/<id>/{tactical-model.json,design.md,api/*.yaml,events/*.json,adapters/*.md}`, `adr/*.md`
- **Gate** every aggregate declares ≥1 invariant [`trace-lint.py --stage 5`]; every design clause cites a Behavior ID [same]; no orphan Behavior IDs in this Slice [same]; every legacy Interface in scope has a named adapter owner [same]; **[record]** architecture review approval, bound to artifact version hash, covering the judgment criterion *"no invariant requires a synchronous call to a sibling aggregate"*
- **Why JIT** designing every Slice up front is waterfall and discards everything learned from Slices already delivered.

### Stage 6 — Verification Design (per Slice)

- **Command** `/rover-verify <slice-id>`
- **Mode** adversarial — generator and `test-adversary` in a loop
- **Activities** characterization suite at the **protocol boundary** covering happy paths, failure paths, timeouts, partial completion, and **event emission** (which events, what order, what partition keys); consumer-driven contract tests; architecture fitness functions including adapter/domain separation; observability spec
- **Outputs** `slices/<id>/verification/{characterization/*,contracts/*,fitness/*,observability-spec.md,coverage.json,harness.lock}`
- **Gate** Redaction Policy verdict = GO for every Interface in this Slice [`trace-lint.py --stage 6`]; characterization coverage of this Slice's Behaviors ≥ threshold [same]; failure-path Behaviors covered, reported separately from happy-path [same]; all fitness functions green **against the existing system** [`run-fitness.py`]; `harness.lock` written [`validate-artifacts.py --stage 6`]
- **Note** fitness functions that fail against the system you already have are wrong functions, not findings.

### Stage 7 — Execution (per Slice)

- **Command** `/rover-execute <slice-id>`
- **Mode** dispatched. ContextRover does **not** author the target implementation — it dispatches to the team's existing tooling, tracks state, runs the harness, enforces the gate, and records the audit trail.
- **Outputs** target source (outside `.contextrover/`); `slices/<id>/execution-log.jsonl`; state transitions
- **Gate** `harness.lock` hash unchanged since Stage 6, or a recorded re-approval exists [`validate-artifacts.py --stage 7`]; full characterization suite green [harness runner]; contract tests green [same]; fitness functions green, including no domain logic in adapter packages and no adapter types in domain packages [`run-fitness.py`]
- **Terminal state** Slice → `Accepted`
- **Failure modes** business logic leaking into adapters, which recreates two implementations of the same behavior on day one

### Stage 8 — Transition (per Modeled Context)

- **Command** `/rover-transition <context-id>`
- **Precondition** every Slice in this Context is `Accepted`
- **Activities** shadow in compare-only mode (domain logic executes fully, effecting adapters stubbed, decisions diffed), canary, progressive cutover, decommission of superseded services; in parallel, the Consumer Migration Workstream retires legacy Interfaces
- **Outputs** `contexts/<id>/{cutover-plan.json,diff-reports/*,decommission-checklist.md}`, `retirement.json` updated
- **Gate** diff rate below threshold at each step [`status-report.py`]; SLO gates hold [same]; superseded services decommissioned [checklist, **[record]**]; per Interface, zero traffic for N days before retirement [`status-report.py`]
- **Sequencing** by blast radius — read-only and non-effecting Contexts first, state-mutating and externally-effecting last.

---

## 4. Consumer Migration Workstream

Cross-cutting, owned by the Engagement directly (not by any Context). Starts once Stage 5 publishes new contracts for a Slice and runs in parallel with everything after. **It never gates Stages 6–8.**

Produces per-consumer migration guides (showing the call-count reduction evidenced by Stage 1 sequence analysis), deprecation notices, and Retirement Register maintenance. Completion criterion: legacy surface decommissioned. Its owner is the sunset authority named at intake.

Interfaces with `sunset_authority: null` are permanent in practice. The report must surface that count prominently.

---

## 5. State model

```
Engagement:  Intake → Discovering → Modeled → Planned → Delivering → Transitioning → Closed
Context:     Proposed → Approved → Building → Ready → Shadowing → Canary → Cutover → Decommissioned
Slice:       Outlined → Designed → OracleFrozen → Building → Accepted
Workstream:  Open → Active → Complete
```

`OracleFrozen` is entered at the Stage 6 gate and is what makes the harness lock meaningful: a Slice cannot enter `Building` without a frozen oracle.
