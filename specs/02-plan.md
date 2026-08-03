# Build Plan — contextrover

How to satisfy `01-spec.md`. Layout, formats and decisions are fixed here. The builder agent does not choose them.

---

## 1. Verified file formats

*Confirmed against current Claude Code documentation. Do not look these up again.*

**Plugin manifest** — `.claude-plugin/plugin.json` (required, at this exact path):

```json
{
  "name": "contextrover",
  "description": "Domain-Driven Modernization: re-decompose N services into M bounded-context-aligned services with no unadjudicated behavioral change.",
  "//": "This description is normative. Do not substitute 'zero behavioral change' — see 09-glossary.md §4.",
  "version": "0.1.0",
  "author": { "name": "" }
}
```

**Component directories live at plugin root, NOT inside `.claude-plugin/`:** `commands/`, `agents/`, `skills/`, `hooks/`, `scripts/`. Optional `.mcp.json` at root. Use kebab-case for every file and directory.

**Subagent** — `agents/<name>.md`, YAML frontmatter then the system prompt as markdown body:

```markdown
---
name: sync-surface-extractor
description: Inventories synchronous HTTP interfaces by reading route declarations. Use during Stage 1 discovery.
tools: Read, Grep, Glob
model: sonnet
---

<system prompt body>
```

Frontmatter fields available: `name`, `description`, `tools`, `disallowedTools`, `model` (`sonnet` | `opus` | `haiku` | `inherit`), `permissionMode`, `maxTurns`, `skills`, `mcpServers`.

**Skill** — `skills/<name>/SKILL.md` with frontmatter `name` and `description`, then instructions.

**Command** — `commands/<name>.md`. The slash command name derives from the filename.

**Hooks** — `hooks/hooks.json`.

---

## 2. Repository layout

```
contextrover/
├── .claude-plugin/plugin.json
├── README.md
├── LICENSE                          MIT
├── .gitignore                       charter.md, .contextrover/, __pycache__/
├── charter.template.md
├── stages.json                      agent roster per stage, keyed by oracle_strategy (seam S1.6)
├── commands/
│   ├── rover-init.md                Stage 0
│   ├── rover-discover.md            Stage 1
│   ├── rover-model.md               Stage 2
│   ├── rover-outline.md             Stage 3
│   ├── rover-roadmap.md             Stage 4
│   ├── rover-design.md              Stage 5   <slice-id>
│   ├── rover-verify.md              Stage 6   <slice-id>
│   ├── rover-execute.md             Stage 7   <slice-id>
│   ├── rover-transition.md          Stage 8   <context-id>
│   ├── rover-migrate.md             Consumer Migration Workstream driver
│   ├── rover-status.md              roll-up report
│   └── rover-project.md             explicit projection to a connector
├── agents/                          all read-only: tools: Read, Grep, Glob
│   ├── sync-surface-extractor.md
│   ├── async-surface-extractor.md
│   ├── behavior-extractor.md
│   ├── dependency-mapper.md
│   ├── consumer-mapper.md
│   ├── call-sequence-analyst.md
│   ├── change-coupling-analyst.md
│   ├── divergence-detector.md
│   ├── redaction-policy-assessor.md
│   ├── boundary-proposer.md         opus
│   ├── spec-critic.md               opus
│   └── test-adversary.md            opus
├── skills/                          one per artifact kind — see T12
├── packs/
│   ├── PACK-INTERFACE.md
│   ├── java/PACK.md
│   ├── go/PACK.md
│   └── python/PACK.md
├── adapters/
│   ├── ADAPTER-INTERFACE.md
│   ├── issue-tracker.md
│   ├── wiki.md
│   └── vcs.md
├── knowledge/
│   ├── ddd-reference.md
│   └── modernization-knowledge-store.md
├── schemas/*.schema.json            see 04-schemas.md
├── hooks/hooks.json
├── scripts/
│   ├── validate-artifacts.py
│   ├── trace-lint.py
│   ├── status-report.py
│   ├── build-graph.py
│   ├── graph-query.py
│   ├── render-report.py
│   ├── run-fitness.py
│   └── resolve-identity.py
├── settings/
│   ├── discovery-profile.json
│   └── authoring-profile.json
└── fixtures/sample-estate/
```

**Deliberately absent in v1:** observability and chat connectors, a Contexture exporter, any LSP discovery path. See `12-extension-seams.md`.

---

## 3. Working directory in the target repo

Its own git repository (`08-knowledge-and-reporting.md` §2).

```
.contextrover/
├── state.json                  engagement / context / slice / workstream ledger
├── intake.json
├── gates.jsonl                 append-only gate audit trail
├── workstreams.json
├── inventory/
│   ├── interfaces.json  behaviors.json  divergences.json
│   └── coupling.json    sequences.json  redaction-policy.json
├── retirement.json
├── consensus/*.json            mechanical multi-pass output
├── adjudications/*.json        human decisions
├── passes/<stage>/<k>/         raw per-pass output, retained as adjudication evidence
├── model/                      contexts.json, context-map.json, variation-policy.json
├── slices/<id>/                prd.md, acceptance-criteria.json, test-approach.md,
│                               size.json, tactical-model.json, design.md,
│                               api/, events/, adapters/, verification/, harness.lock
├── contexts/<id>/              cutover-plan.json, diff-reports/, decommission-checklist.md
├── graph/                      nodes.jsonl, edges.jsonl (derived)
├── report/index.html           derived, never a gate
└── projections/<connector>.json
```

`passes/` is retained deliberately — the raw disagreement between passes is the evidence behind every Adjudication, and in a regulated setting it is what makes the judgment auditable.

---

## 4. Fixed decisions

| # | Decision | Rationale |
|---|---|---|
| D1 | Artifacts are JSON; markdown is generated from JSON | Lint and coverage operate on data (Constitution C7) |
| D2 | ID formats: `BHV-0001`, `IFC-SYNC-0001`, `IFC-ASYNC-0001`, `DVG-0001`, `CTX-0001`, `ADJ-0001`, `SLC-0001`, `WS-0001` | Sequential and stable. Never renumber; append only (REQ-31) |
| D3 | Default ensemble K = 3, configurable | Balance of signal and cost (C6) |
| D4 | Framing variants: `by-routes`, `by-tests`, `by-call-sites` | Independence via vantage point, not model tier (C6) |
| D5 | Python 3 stdlib only for scripts | No installs, no network (C5, REQ-73) |
| D6 | Discovery agents: `tools: Read, Grep, Glob` — always explicit | Subagents cannot prompt for permission (C3) |
| D7 | Discovery agents `model: sonnet`; `boundary-proposer`, `spec-critic`, `test-adversary` `model: opus` | Breadth cheap, judgment strong |
| D11 | Identity resolution is a deterministic script, never an agent | Byte-identical IDs across runs (REQ-31a) |
| D8 | Adapters are mapping specs consuming MCP tools, not integrations | Keeps the plugin dependency-free (REQ-43/44) |
| D9 | Projection is an explicit command, never automatic | External writes are side effects (REQ-47) |
| D10 | Stage commands orchestrate only | No business logic in commands (C9) |

---

## 5. Stage-to-component map

| Stage | Command | Agents | Gate scripts |
|---|---|---|---|
| 0 Intake | `rover-init` | — | `validate-artifacts.py --stage 0` |
| 1 Discovery | `rover-discover` | 9 discovery agents ×K | `validate-artifacts.py`, `trace-lint.py --stage 1` |
| 2 Strategic Design | `rover-model` | boundary-proposer ×K | `trace-lint.py --stage 2` |
| 3 Solution Outline | `rover-outline` | — | `trace-lint.py --stage 3` |
| 4 Delivery Roadmap | `rover-roadmap` | — | `trace-lint.py --stage 4` |
| 5 Tactical Design | `rover-design` | spec-critic | `trace-lint.py --stage 5` |
| 6 Verification Design | `rover-verify` | test-adversary | `trace-lint.py --stage 6`, `run-fitness.py` |
| 7 Execution | `rover-execute` | — | `validate-artifacts.py --stage 7`, harness runner, `run-fitness.py` |
| 8 Transition | `rover-transition` | — | `status-report.py` |
| — Consumer Migration | `rover-migrate` | — | `status-report.py` |

Consensus aggregation and adjudication-record writing happen in the **main session** at Stages 1 and 2, never in a subagent — a subagent cannot surface an approval prompt and an Adjudication requires a human decider.

---

## 6. Build order rationale

Schemas first — every other component references them, and building agents before their output contract is defined produces agents that emit unvalidatable text. Then, in order: **scripts (the gates) → agents → skills → packs → connectors → profiles and stage config → commands.**

Commands are last because they orchestrate everything else and are the thinnest layer. `03-tasks.md` is the authoritative order; this paragraph is explanation, not a second ordering.

**Note:** the layout in §2 is the v1 target and includes files added by `08-knowledge-and-reporting.md` (`build-graph.py`, `graph-query.py`, `render-report.py`, `run-fitness.py`, `.contextrover/graph/`), plus `knowledge/`, `fixtures/` and `stages.json`. T01's "matches §2" acceptance means this complete list.
