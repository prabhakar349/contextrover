# Intake Specification — contextrover

Stage 0 is not just "write a constitution." It is a **structured intake interview** that makes the tool self-configuring: it determines which agents can run, which language packs load, which adapters activate, and which risks must be flagged before any analysis starts.

Output: `.contextrover/intake.json`, which every downstream stage reads.

---

## 1. Principles

- **P1 — Conversational, one question at a time.** Never present a wall of questions. The operator is thinking while answering; a form suppresses that.
- **P2 — Never ask for something the tool cannot use.** Probe capability *first*, then ask configuration questions only for capabilities that are actually present. Collecting a project key for an unreachable system wastes the operator's time and creates a false expectation.
- **P3 — Every answer is recorded with provenance.** `answered` | `unknown` | `deferred`, with who said it and when. `unknown` is a legitimate answer that propagates into risk flags.
- **P4 — Resumable.** Intake can be re-entered; existing answers are pre-filled and confirmed rather than re-asked.
- **P5 — Absence is never fatal.** Missing capabilities degrade the plan and raise flagged risks; they never block the run (REQ-44).
- **P6 — Intake drives the plan.** The output is not a questionnaire archive. It determines which agents are dispatched in Stage 1 and which gates are enforceable.

---

## 2. Interview sections

### A — Estate

| # | Question | Drives |
|---|---|---|
| A1 | Where do the services live? (paths or repo URLs) | Discovery scope |
| A2 | How many services are in scope? | Ensemble sizing |
| A3 | Which languages? | Which packs load (REQ-51) |
| A4 | Target language, if different from source? | Confirms packs are independent (REQ-53) |
| A5 | Is there an orchestrator or front-facing service? | Boundary hypothesis — an orchestrator fronting small services is the mechanism-boundary signature |
| A6 | Which protocols? (HTTP, gRPC, Kafka, SQS, …) | Which surface extractors run |

### B — Evidence sources *(the section that determines what is actually knowable)*

| # | Question | If absent |
|---|---|---|
| B1 | Is full commit history available? | `change-coupling-analyst` cannot run → boundary decisions lose their empirical input (DR2). **Flag as high risk.** |
| B2 | Are HTTP access logs retained? For how long? | `call-sequence-analyst` degrades to static analysis → new API design loses usage evidence (§5.4) |
| B3 | Is there a schema registry? | Async schema fidelity unverifiable |
| B4 | Is consumer-group / lag telemetry retained? | **`consumers_complete` can never be true.** Flag as the top risk in the Stage 1 report — event-contract preservation is being done blind |
| B5 | Can production request/response pairs be captured and replayed? | Characterization corpus must come from synthetic inputs; coverage will be materially lower |
| B6 | What does data-handling policy permit for captured traffic? | Determines masking and storage requirements |
| B7 | Are there existing integration or contract tests? | Additional evidence framing for the ensemble |

**B4 deserves special handling.** If the answer is no, the intake must say so plainly, in these terms: *"Unknown event consumers cannot be enumerated. Any legacy topic may have readers we cannot see, including replay consumers that are not running today. Dual publishing must continue indefinitely until this is resolved."* Then record it as a blocking risk on the the Consumer Migration Workstream gate, not the Stage 1 gate — it does not stop discovery, it stops retirement.

### C — Constraints

| # | Question | Drives |
|---|---|---|
| C1 | Is this an approval-gated environment? | Whether unattended discovery profile is usable |
| C2 | Which model tiers are available to the CLI here? | Ensemble configuration |
| C3 | Ensemble budget — K value? (default 3) | Stage 1 pass count |
| C4 | Air-gapped? | Disables all adapter probes |
| C5 | Timeline and any freeze windows | Rollout sequencing in Stage 8 |

### D — Integrations *(capability probe — see §3)*

### E — Governance

| # | Question | Drives |
|---|---|---|
| E1 | Has the success metric been agreed? (*"zero boundaries that do not correspond to a bounded context"*, not a service count) | If no → **first recommended action**, before Stage 2 produces a number |
| E2 | Was a target service count mandated? By whom? | Surfaces the §4.3 negotiation early |
| E3 | Who approves boundary decisions? | Stage 2 adjudication owner |
| E4 | Who can mandate an interface retirement date? | Sunset authority. If null, the Consumer Migration Stream has no completion mechanism |
| E5 | Who signs each stage gate? | Approval matrix in the constitution |

E1 and E2 together are the political early-warning system. If a count was mandated and the metric has not been reframed, the intake output must say so explicitly as a recommended first action.

### F — Delivery Capacity

Organization-specific and unknowable from code. Feeds the Stage 4 forecast (`11-estimation.md`).

| # | Question | Default if unknown |
|---|---|---|
| F1 | Engineers actually available to this engagement (not headcount) | — |
| F2 | **Qualified reviewers** for this codebase | — |
| F3 | Maximum PR size policy, including tests | 500 lines |
| F4 | PRs a reviewer completes per day | 3 |
| F5 | CI cycle time, and flake rate | — |
| F6 | Deploys to production per week | — |
| F7 | Change-approval lead time per production change | 0 days |
| F8 | Test environment availability and contention | — |
| F9 | Walking Skeleton duration — infra, data stores, pipeline, observability, security | 2 weeks |
| F10 | Freeze windows and holidays in the horizon | — |
| F11 | Onboarding ramp for anyone not already on the codebase | — |

F2, F4 and F7 determine the date. F1 rarely does — review capacity is the binding constraint, not authoring capacity. Every default used because the answer was unknown must appear in `roadmap.json.capacity.assumptions_used`.

---

## 3. Capability probe protocol

Runs during Section D. Ordering is the important part.

```
FOR each integration category (issue tracker, wiki, VCS, observability, chat):

  1. ASK intent
     "Do you want <category> integration? Which system?"
     └─ No → record adapter: disabled. Next category.

  2. PROBE availability
     Check whether the MCP tools named by that adapter's spec are
     present in the current session.
     └─ Do NOT ask the user whether they have it. Detect it.

  3a. AVAILABLE → ask configuration questions, scoped to that system only
      e.g. issue tracker: project key, issue type for tasks, issue type
      for decisions, the field carrying `contextrover-id`
      └─ record adapter: ready

  3b. UNAVAILABLE → do NOT ask configuration questions (P2)
      Emit precise remediation:
        "<System> integration requires the <name> MCP server, which is not
         connected in this session. Connect it with `claude mcp add …` or
         via your connector settings, then re-run /rover-init to enable
         projection. Continuing without it — all artifacts will still be
         produced locally and can be projected later."
      └─ record adapter: unavailable, with the reason

  4. NEVER fail the stage on an unavailable adapter (REQ-44).
```

**Why probe before configuring:** asking for a Jira project key when the Jira MCP server isn't connected produces config that cannot be used and an operator who believes integration is working. The probe result is also recorded, so a later run can tell the difference between "never wanted it" and "wanted it, couldn't reach it."

**Re-probing:** every `/rover-project` invocation re-probes before acting. Availability at intake time does not guarantee availability at projection time.

---

## 4. Intake output

`.contextrover/intake.json`:

```json
{
  "version": "1",
  "completed_at": "2026-08-01T00:00:00Z",
  "operator": "",
  "estate": {
    "repos": [], "service_count": 0,
    "source_languages": [], "target_language": null,
    "has_orchestrator": null, "protocols": []
  },
  "evidence": {
    "commit_history":      { "available": null, "note": "" },
    "access_logs":         { "available": null, "retention_days": null },
    "schema_registry":     { "available": null },
    "consumer_telemetry":  { "available": null },
    "traffic_capture":     { "available": null, "policy_note": "" },
    "existing_tests":      { "available": null }
  },
  "default_oracle_strategy": "characterization",
  "constraints": {
    "approval_gated": null, "available_models": [],
    "ensemble_k": 3, "air_gapped": false,
    "timeline": null, "freeze_windows": []
  },
  "adapters": {
    "issue_tracker": { "intent": "yes|no", "system": null,
                       "status": "ready|unavailable|disabled",
                       "mcp_tools": [], "config": {}, "reason": null }
  },
  "capacity": {
    "engineers": null, "reviewers": null, "pr_size_limit": 500,
    "prs_per_reviewer_per_day": 3, "ci_cycle_minutes": null, "flake_rate": null,
    "deploys_per_week": null, "change_lead_time_days": 0,
    "env_contention": null, "walking_skeleton_days": 10,
    "freeze_windows": [], "onboarding_ramp_days": null
  },
  "governance": {
    "success_metric_agreed": null, "mandated_count": null,
    "mandate_owner": null, "boundary_approver": null,
    "sunset_authority": null, "gate_approvers": {}
  },
  "derived": {
    "agents_enabled":  [],
    "agents_disabled": [{ "agent": "", "reason": "" }],
    "packs_loaded":    [],
    "risks":           [{ "id": "", "severity": "high|medium|low",
                          "statement": "", "blocks_gate": null }]
  }
}
```

The `derived` block is computed, not asked. It is the intake's actual product — everything above it is input.

---

## 5. Derived risk rules

Computed automatically from the answers. These are fixed; the builder agent implements them exactly.

| Condition | Risk | Severity | Blocks |
|---|---|---|---|
| `consumer_telemetry.available = false` | Unknown async consumers cannot be enumerated; legacy topics may have invisible readers | **high** | the Consumer Migration Workstream gate |
| `commit_history.available = false` | Boundary proposals lack empirical coupling evidence — the documented weakness of automated DDD (DR2) | **high** | Stage 2 gate (warn) |
| `traffic_capture.available = false` | Characterization corpus is synthetic; coverage will be materially lower | **high** | Stage 6 gate (warn) |
| `access_logs.available = false` | New API design loses observed-usage evidence; risk of designing contracts nobody wants | medium | — |
| `schema_registry.available = false` | Async payload fidelity unverifiable | medium | — |
| `success_metric_agreed = false` **and** `mandated_count` is set | Analysis will likely contradict the mandate with no agreed reframing | **high** | Stage 2 gate (warn) |
| `sunset_authority = null` | the Consumer Migration Stream has no completion mechanism; legacy surface is permanent by default | **high** | the Consumer Migration Workstream gate |
| `air_gapped = true` | All projections disabled; artifacts local only | low | — |

Every high risk appears at the top of `/rover-status` until resolved or explicitly accepted with a recorded rationale.

---

## 6. Intake completion

Intake is complete when every section A–F has an answer or an explicit `unknown`, `derived` is computed, and the operator has seen the risk summary and either resolved or accepted each high risk.

`/rover-init` then writes `intake.json`, updates `state.json` stage 0 to `complete`, appends to `gates.jsonl`, and prints:

- Which agents will run in Stage 1, and which are disabled and why
- Which packs will load
- Which adapters are ready, unavailable, or disabled
- The high-risk list
- The single recommended first action (usually E1, if the success metric has not been reframed)
