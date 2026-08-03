# Ubiquitous Language — NORMATIVE

**Precedence:** this document outranks every other file in the pack on terminology. Where `00`–`08` use a superseded term, the term here wins and the older usage is a defect to be corrected, not a variant to be preserved. Concepts, requirements and formats in the other documents are unaffected.

Derived from the ContextRover domain model (`../contextrover-domain-model.md`), with three deviations recorded in §5.

---

## 1. The delivery vocabulary (previously the worst offender)

| Term | Definition | Notes |
|---|---|---|
| **Engagement** | One application of ContextRover to one estate. The top-level aggregate. | Owns cross-cutting workstreams directly, not only via contexts (§5.2) |
| **Bounded Context** | A boundary within which one model and one language apply. The unit of architectural decision. | Standard DDD |
| **Slice** | A thin end-to-end deliverable that exercises real behavior across all layers. The unit of build, verification and rollout. | **Use `Slice`. `Vertical Slice` is dropped as a redundant synonym.** |
| **Use Case** | A named goal a user or system achieves. A Slice delivers one or more. | A Use Case is not independently deliverable; a Slice is |
| **Capability** | A clustering heuristic used during Strategic Design to group related behavior before contexts are settled. | **Not tracked. Not a state-bearing entity.** Once contexts exist, capabilities have done their job |
| **Increment** | A scheduled tranche of Slices on the roadmap. | Increment 0 is always the Walking Skeleton |
| **Walking Skeleton** | The first Increment: thin end-to-end implementation exercising every architectural component, with observability, monitoring, security and pipeline live. Permanent — it grows into the system. | Cockburn. Synonyms *tracer bullet*, *steel thread*. **Not "scaffolding"** — scaffolding is discarded |
| **Migration Wave** | A batch of consumers moved together during Transition. | Confined to Transition. Do not use "wave" elsewhere |
| **Stage** | One of the nine steps of the journey (0–8), defined in `07-stages.md`. | **`Phase` is dropped entirely.** The old phase numbering is *not* a renumbering — see §6 |

**Removed entirely: `Component`.** It carried no distinct meaning. Where an earlier document says "component", read *Slice* if it refers to delivery, or *service* if it refers to a deployable.

---

## 2. Evidence and decision vocabulary

| Term | Definition |
|---|---|
| **Behavior** | An atomic observed fact about how the system behaves, with a stable ID and evidence. The unit of traceability. |
| **Interface** | A synchronous endpoint or an asynchronous stream, published or consumed. |
| **Divergence** | Two or more sources disagreeing about the same concept. Classified as **Policy**, **False Cognate**, or **Defect**. |
| **False Cognate** | Two things that look like the same concept but are not — they belong to different bounded contexts. | 
| **Consensus Run** | The mechanical multi-pass process: K independent passes, union, partition into found-by-all / found-by-some / found-by-one. Produces evidence. | 
| **Adjudication** | The **human** decision over a Consensus Run's output, with named decider and rationale. Produces authority. |
| **Oracle Strategy** | How correctness is established for a Slice: **Characterization** (brownfield — the existing system is the oracle) or **Specification** (greenfield — human-authored acceptance criteria are the oracle). |
| **Evidence Graph** | The derived read model over all artifacts. Never authoritative; regenerated from artifacts, which win on conflict. |
| **Redaction Policy** | Which volatile fields must be masked for comparison to be meaningful, and whether that is feasible at all. |

**Consensus Run and Adjudication were previously conflated.** They are different: one is a computation, the other is an accountable act. A Consensus Run can be re-executed; an Adjudication cannot be re-executed, only superseded.

---

## 3. Governance and integration vocabulary

| Term | Definition |
|---|---|
| **Engagement Charter** | The organization-specific, private, gitignored file supplying standards, compliance baselines, approval matrix and success metric. **Previously called "constitution."** |
| **Build Constitution** | The principles governing how the *plugin itself* is built (`00-constitution.md`). **Unrelated to the Engagement Charter — do not merge these.** |
| **Access Probe** | Detection of whether a required MCP tool is present in the session. **Previously "capability probe"** — renamed to avoid collision with Capability. |
| **Connector** | An external system integration surface (MCP server) that ContextRover consumes. |
| **Adapter** | A translation layer in the *target architecture* between a contract and the domain core. |
| **Projection** | A one-way, idempotent export of an artifact into an external system, keyed by `contextrover-id`. |
| **Gate** | A machine-checkable exit criterion for a Stage. If a human must read and form an opinion, it is not a Gate. |
| **Language Pack** | Programming-language-specific discovery and verification conventions (Java, Go, Python). |

---

## 4. The claim, restated

**Do not say "zero behavioral change."** It is false the moment a Divergence is classified as a Defect, because a Defect is a known difference deliberately preserved or deliberately corrected later.

**Say: "no unadjudicated behavioral change."** Every difference between old and new is either absent, or recorded with a named human owner and a rationale. That claim survives audit; the other does not.

---

## 5. Deviations from the domain model

Three of the model's rulings are **not** adopted, with reasons:

**5.1 `Language Pack` is retained.** The model proposed renaming it to *Glossary*, which collides directly with the ubiquitous-language glossary artifact produced in Tactical Design. Two unrelated things would share a name. Language Pack is unambiguous and stays.

**5.2 The hierarchy is amended rather than kept strict.** The model is right that `Engagement → Context → Slice → Use Case` breaks for the Walking Skeleton and for consumer migration, both of which are cross-cutting. Amendment: **an Engagement owns Workstreams directly.** A Workstream is either context-scoped (contains Slices) or cross-cutting (Walking Skeleton, Consumer Migration). Slices belong to Workstreams, not to Contexts.

**5.4 `oracle_strategy` sits on the Slice, not the Engagement.** The model fixes Mode at Engagement level and treats it as immutable. This pack places it per Slice, permitting mixed engagements. Rationale: a re-decomposition frequently adds genuinely new capability alongside preserved behavior, and forcing two Engagements to model one domain splits the context map. Cost: the "one oracle per engagement" invariant is lost and reporting must aggregate two denominators. Accepted knowingly; v1 permits only `characterization`, so the cost is not yet paid (`12-extension-seams.md` §1).

**5.3 Discovery and Verification remain separable in tooling, merged in language.** The model's argument — a characterization test is a Behavior made executable, so they share a language and belong in one context — is accepted for the *domain model*. But the Stage boundary between them stays, because the Redaction Policy GO/NO-GO decision sits between them and must be a gate. One bounded context, two stages.

---

## 6. Supersession map

For an implementer reading `00`–`08`:

**The old seven-phase model was not renumbered — it was restructured.** Any document still using phase numbers is superseded by `07-stages.md`. For historical reading only:

| Old phase | Became |
|---|---|
| Phase 0 Intake | Stage 0 |
| Phase 1 Discover | Stage 1 |
| Phase 2 Domain modeling | Stage 2 |
| Phase 3 Specify | **split** → Stage 3 (Solution Outline) + Stage 5 (Tactical Design) |
| Phase 4 Verification design | Stage 6 |
| Phase 5 Implement | Stage 7 |
| Phase 6 Converge | Stage 8 |
| Phase 7 Migrate consumers | **Consumer Migration Workstream** — no longer a stage (`07-stages.md` §4) |

Other supersessions:

| If you read | Understand it as |
|---|---|
| Track A / Track B | Build Stream / Consumer Migration Stream |
| constitution (engagement-level) | Engagement Charter |
| Constitution C1–C10 | Build Constitution — unchanged, different thing |
| capability probe | Access Probe |
| maskability | Redaction Policy |
| knowledge graph | Evidence Graph |
| "context-separation" divergence | False Cognate |
| vertical slice | Slice |
| component | Slice, or service |
| wave | Increment (planning) or Migration Wave (transition) |
| "zero behavioral change" | "no unadjudicated behavioral change" |
