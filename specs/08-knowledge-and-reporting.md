# Knowledge Store, Artifact History, and Reporting

Three additions to the plugin: a queryable knowledge graph, version-controlled artifacts, and a rich HTML program report.

---

## 1. Knowledge stores — there are two, and they are different

| | **Method knowledge base** | **Project knowledge graph** |
|---|---|---|
| Lives in | `knowledge/` in the plugin repo | `.contextrover/graph/` in the target repo |
| Contains | Curated modernization prior art, patterns, citations | Facts about *this* estate |
| Ships publicly | Yes | Never — it is organization data |
| Purpose | Grounds agent prompts in established practice | Answers "what depends on this?" |
| Updated | With the plugin | Every stage |

### 1.1 Method knowledge base (`knowledge/`)

Curated corpus organized by the stage it informs, each entry annotated with *what to take* and *what to leave*. Agents reference it by path in their system prompts rather than carrying the content inline — this keeps agent definitions small and lets the corpus grow without touching them.

Seed content is supplied. It must stay strictly domain-agnostic and citation-based (Constitution C4).

### 1.2 Project knowledge graph (`.contextrover/graph/`)

**Rationale.** The traceability spine already *is* a graph. Storing it as one makes lint queries, impact analysis and reporting fall out of the data model instead of requiring bespoke traversal code for each new question. Precedent: Thoughtworks' CodeConcise pairs LLMs with a code-derived knowledge graph for exactly this purpose.

**Format.** Two JSON Lines files. No graph database — stdlib-queryable, diffable, and installable anywhere (Constitution C5).

```
.contextrover/graph/nodes.jsonl
.contextrover/graph/edges.jsonl
```

**Node types:** `Service`, `Interface`, `Behavior`, `Context`, `Aggregate`, `Consumer`, `Divergence`, `Test`, `Commit`, `Topic`, `Adapter`.

**Edge types:** `exposes`, `implements`, `depends-on`, `publishes`, `consumes`, `co-changes-with`, `belongs-to`, `covers`, `diverges-from`, `retires`, `derived-from`.

```json
{"id":"BHV-0042","type":"Behavior","label":"...","confidence":"high","agreement":1.0,"phase_added":1}
{"from":"BHV-0042","to":"CTX-0003","type":"belongs-to","evidence":"ADJ-0007"}
```

**Rules.**

- The graph is **derived**, never authored. `scripts/build-graph.py` regenerates it from `inventory/`, `model/`, `spec/`, `verification/`. If the graph and the artifacts disagree, the artifacts win.
- Every edge carries provenance — which artifact or adjudication asserted it.
- Regenerated at every gate; cheap enough to rebuild from scratch each time, which avoids incremental-update bugs entirely.

**Queries the graph makes trivial** (`scripts/graph-query.py`):

- Impact — everything reachable from a service or topic
- Orphans — behaviors with no context, contexts with no behaviors
- Boundary spans — behaviors touching more than one target service
- Coverage — behaviors with no `covers` edge from a Test
- Consumer blast radius — who breaks if this interface changes
- Coupling clusters — components that co-change, as boundary evidence

**Optional enrichment — Serena / LSP.** When a Language Server Protocol tool such as Serena is available as an MCP server, discovery agents should prefer symbol-level extraction over pattern matching. LSP gives symbol truth across 30+ languages from one interface, which is materially better than per-framework grep patterns. Detected via the capability probe (`06-intake.md` §3); absent, packs fall back to pattern discovery. Deferred to v2 (`12-extension-seams.md` §3). v1 packs declare `discovery_method: pattern`; the obligation is that extraction strategy lives in the pack, never inline in an agent prompt (seam S3.2), so LSP can be added without touching agents.

---

## 2. Artifact history — `.contextrover/` is its own git repository

`/rover-init` runs `git init` inside `.contextrover/`. It is a **separate repository from the source estate**, so evidence history never entangles with application history.

**What this buys:**

- Full history of how understanding evolved — a behavior record's `git blame` shows which pass and which adjudication produced it
- Diffable artifacts between gates: *what changed in our understanding since last week* becomes one `git diff`
- Recoverable state after a bad stage re-run
- A push target later, if the team wants evidence hosted centrally

**Commit protocol.** Automatic commit at every gate, never mid-stage:

```
stage(1): gate pass — 247 behaviors, 38 interfaces, agreement 0.82

Artifacts:
  inventory/behaviors.json  sha256:...
  inventory/interfaces.json sha256:...
Gate: trace-lint.py exit 0
Operator: <from intake>
```

Tag on stage completion: `stage-1-complete`, `stage-2-complete`, …

**Relationship to `gates.jsonl`:** the JSONL is the append-only audit log — what happened, when, with what result. Git is the content history — what the artifacts actually said at that moment. Regulated environments want both; the log proves sequence, the repository proves content.

**Interaction with the source repo's `.gitignore`:** the source repo ignores `.contextrover/` (Task T01). The nested repository is intentional and must be documented in the README, since a nested `.git` surprises people.

---

## 3. HTML program report

`scripts/render-report.py` → `.contextrover/report/index.html`

### 3.1 Hard constraints

- **Single self-contained file.** All CSS, JS and data inlined. No CDN, no external fonts, no network requests — the report must open from disk in an air-gapped environment (Constitution C5, REQ-73).
- **Stdlib only.** No templating engine, no chart library. Charts are hand-emitted inline SVG.
- **Regenerated at every gate**, plus on demand via `/rover-status --html`. No daemon, no watch mode — "real-time" here means *current as of the last gate*, and the report states its generation timestamp prominently so nobody mistakes it for live.
- **Data embedded as a JSON blob** in a `<script type="application/json">` tag, rendered by inline JS. Keeps the generator simple and makes the data extractable by anyone who wants it.

### 3.2 Report sections

**Header — the program at a glance**

- N services in → M proposed out (or *"M undetermined — Stage 2 pending"*, never a guess)
- Current stage, with the stage pipeline rendered as a progress rail
- Generation timestamp and the git SHA of `.contextrover/` at render time
- Build Stream conformity % and Consumer Migration Stream adoption % as two separate gauges — **never blended** (REQ-13)

**Service inventory**

One card per source service: name, language, repository link (from intake A1, rendered as a clickable link where a URL was supplied), interface counts split sync/async, behavior count, proposed target context, and current stage for that service. Sortable and filterable.

The per-service stage is the answer to *"which slice is where?"* — different contexts move through Stages 5–7 at different speeds, and a single program-level stage number hides that.

**Stage timeline**

Each stage: status, start/end, gate result, artifact count, operator, and a link to the gate's commit in `.contextrover/`.

**Coverage**

- Behaviors by status: uncovered / covered / passing
- Ensemble agreement histogram — the distribution of found-by-all vs. found-by-one
- Failure-path coverage shown **separately** from happy-path coverage, because a suite that looks complete while skipping failure paths is the characteristic silent failure of this class of migration

**Divergences**

Grouped by classification: unclassified (red — blocks the Stage 2 gate), policy, false-cognate, defect. Each with its decision owner and, where projected, a link to the external issue.

**Risks**

High risks from intake §5 that remain unresolved, each with the gate it blocks. Interfaces with `sunset_authority: null` counted prominently — that number is the leading indicator that the Consumer Migration Stream will never finish.

**Retirement register**

Full table: interface, type, known consumers, status, sunset date, sunset authority, last observed traffic, days at zero traffic.

### 3.3 Design notes

- Every number must be **traceable to an artifact**. Hovering or clicking a figure reveals which file produced it. A dashboard whose numbers cannot be traced is a dashboard nobody trusts twice.
- Unknowns render as explicit "unknown" with the recorded reason — never as zero, never as blank. Blank reads as "fine"; unknown reads as unknown (Constitution C10).
- Prints legibly. These reports end up in steering decks.

---

## 4. Build tasks

These are already incorporated into `03-tasks.md` as T06, T07, T08 and the artifact-repository requirement in T16. Retained here as the rationale behind them:

**T05a — `scripts/build-graph.py`** — regenerates `nodes.jsonl` and `edges.jsonl` from artifacts. Idempotent; full rebuild each run. *Accept:* produces a valid graph from a fixture; rebuilding twice yields byte-identical output.

**T05b — `scripts/graph-query.py`** — the six named queries in §1.2, `--format text|json`. *Accept:* each query returns correct results against a fixture with a seeded orphan and a seeded boundary span.

**T05c — `scripts/render-report.py`** — the HTML report. *Accept:* output is a single file that opens offline with no network requests (verify: no `http://`, `https://`, or `//cdn` in the emitted HTML except as user-supplied repository links); shows unknowns as unknowns; Build Stream and Consumer Migration Stream gauges are separate.

**T11c — Artifact repository initialization** — `/rover-init` runs `git init` in `.contextrover/`, writes its `.gitignore`, and makes the initial commit. Every gate commits with the §2 message convention and tags on stage completion. *Accept:* two consecutive stage runs produce two commits with parseable messages and artifact hashes.
