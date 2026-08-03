# DDD Reference — operational grounding for agents

Canonical domain-driven design, written as **rules an agent applies**, not as a reading list. Citations are at the end; the rules come first because that is the order an agent needs them.

**Which agents load this:** `boundary-proposer` (§§1, 4, 6), Tactical Design skills (§2), Strategic Design command (§§1, 3), `spec-critic` (§6).

---

## 1. Strategic design

### 1.1 Subdomain classification

Classify every candidate area before deciding how much effort it deserves.

| Type | Definition | Implication |
|---|---|---|
| **Core** | Where the organization differentiates. Losing it loses the business. | Model it carefully. Own it. Best people. |
| **Supporting** | Necessary, specific to this business, but not differentiating. | Model adequately. Build simply. |
| **Generic** | Solved everywhere the same way (auth, notifications, payments rails). | Buy or adopt. Do not model lovingly. |

Applied to re-decomposition: a Generic subdomain that has been split across several services is usually a consolidation with no boundary debate. A Core subdomain split along mechanism lines is the expensive, valuable case.

### 1.2 Bounded Context

A boundary within which a single model applies and every term has exactly one meaning. **The boundary is linguistic before it is technical.**

Operational test: take a candidate term and ask whether it means the same thing on both sides of a proposed line. If it shifts meaning, the line is real. If it does not, you have drawn a line through one context.

A bounded context is not a microservice, a repository, a team, or a database. It may align with any of those — that is a deployment decision, made after the boundary decision.

### 1.3 Context map — the relationship patterns

Every pair of contexts that communicate has exactly one of these relationships. Naming it is mandatory; leaving it unnamed is how integration debt accumulates.

| Pattern | Meaning | Use when |
|---|---|---|
| **Partnership** | Two contexts succeed or fail together; coordinated planning | Genuine mutual dependency, same delivery cadence |
| **Shared Kernel** | A small shared model, jointly owned, changed only by agreement | Rare. Keep tiny. Every addition doubles the coordination cost |
| **Customer–Supplier** | Downstream has a voice in upstream's roadmap | Upstream can and will accommodate downstream needs |
| **Conformist** | Downstream adopts upstream's model wholesale, no translation | Upstream will not negotiate and translation is not worth it |
| **Anticorruption Layer (ACL)** | Downstream translates upstream's model into its own | **The default for integrating a legacy context.** Protects the new model |
| **Open Host Service** | Upstream publishes a general-purpose protocol for many consumers | Many downstreams, upstream cannot special-case each |
| **Published Language** | A well-documented shared interchange format | Paired with Open Host Service |
| **Separate Ways** | No integration at all; duplicate rather than couple | Integration cost exceeds the value of sharing |

**Rule for legacy work:** a heritage system stays in its own bounded context with its own ubiquitous language and is integrated via an ACL. Never merge a legacy context into a new one to "clean it up" — that imports its language and dilutes the new model.

---

## 2. Tactical design

### 2.1 Aggregates — Vernon's four rules

These are the operative rules. An aggregate design that violates them is wrong regardless of how it reads.

1. **Model true invariants in consistency boundaries.** An aggregate exists to enforce a rule that must hold at the end of every transaction. If you cannot state that rule, you do not have an aggregate — you have a data structure.
2. **Design small aggregates.** Prefer one root plus a minimum of tightly-bound parts. Large aggregates cause contention, slow loads and transaction failures.
3. **Reference other aggregates by identity only.** Hold an ID, never an object reference. This is what keeps consistency boundaries honest.
4. **Use eventual consistency outside the boundary.** One transaction modifies one aggregate. Anything else happens via a domain event and a subsequent transaction.

**Derived check used by this framework:** a proposed service must own at least one aggregate root and be able to enforce its invariants without a synchronous call to a sibling. That is rules 1 and 3 restated at the service level, and it is what separates a service from a module.

**The invariant question to ask a domain expert:** *"What must never be true, even for a moment?"* The answer names the aggregate. If nobody can answer, the candidate aggregate is a report, not a model.

### 2.2 Building blocks

| Block | Definition | Test |
|---|---|---|
| **Entity** | Identity persists through state change | Would you still call it the same thing after every attribute changed? |
| **Value Object** | Defined entirely by its attributes; immutable; no identity | Are two with equal attributes interchangeable? Then it is a value |
| **Aggregate Root** | The only entry point to an aggregate; enforces its invariants | Can anything outside reach an internal entity directly? Then the boundary leaks |
| **Domain Event** | Something meaningful that happened, named in the past tense | Would a domain expert recognize the name? `OrderPlaced`, not `OrderTableUpdated` |
| **Command** | An intent to change state, named in the imperative | May be rejected. `PlaceOrder` |
| **Policy** | "When X happens, do Y" — reactive rule connecting event to command | Often the missing piece where logic was scattered across services |
| **Domain Service** | Behavior that belongs to no single entity | Use sparingly; most "services" are misplaced aggregate behavior |
| **Repository** | Collection-like access to aggregates, one per aggregate root | One repository per aggregate root, never per table |

**Anaemic domain model warning:** if aggregates have only getters and setters and all behavior lives in services, DDD has been applied in name only. In re-decomposition this is the most common outcome, because behavior extracted from N services tends to land in a service layer by default.

---

## 3. Modelling techniques

| Technique | What it produces | Best for |
|---|---|---|
| **EventStorming** (Brandolini) | Domain events on a timeline → commands, aggregates, boundaries | Broad discovery with domain experts; the fastest route to boundaries |
| **Domain Storytelling** | Pictographic narratives of actor–work-object interactions | Understanding a workflow precisely, with non-technical experts |
| **Event Modeling** (Dymitruk) | Events, commands, read models on a timeline with UI slices | Specifying a system for build; strong fit for Solution Outline |
| **Bounded Context Canvas** | One-page description of a context: purpose, inbound/outbound messages, ubiquitous language | Documenting an agreed context |
| **Aggregate Design Canvas** | Aggregate name, state transitions, enforced invariants, handled commands, created events | Tactical Design — forces invariants to be stated |
| **Core Domain Charts** | Business differentiation vs. model maturity | Deciding where to invest modelling effort |

**Agent posture on all of these: prepare and capture, never decide.** An agent may generate a first-draft event model from code and populate a canvas. The boundary decision belongs to humans with the practical constraints in their heads — published research on automated DDD finds models produce theoretically valid boundaries while missing coupling and operational cost.

---

## 4. Boundary heuristics

Apply in this order. Earlier rules outrank later ones.

1. **Linguistic** — does a term change meaning across the line? A real shift means a real boundary. This is the strongest signal and the cheapest to test.
2. **Invariant containment** — can each side enforce its invariants alone? If enforcing a rule requires a synchronous call across the line, the line is in the wrong place.
3. **Change coupling** — do these things change together in commit history? Things that change together belong together. Measurable, therefore not debatable.
4. **Data ownership** — does exactly one context own each piece of state? Shared write access across a line means the line is fictional.
5. **Team topology** — can one team own this end to end? Conway's law applies whether or not you plan for it.
6. **Scaling and lifecycle** — different load profiles or release cadences justify splitting an already-valid context. **Never** use this to justify creating one.

Rules 5 and 6 are tiebreakers, not primary criteria. Boundaries drawn from org chart or scaling alone are how mechanism-shaped nanoservices happen in the first place.

---

## 5. Brownfield patterns

| Pattern | Use |
|---|---|
| **Anticorruption Layer** | Default integration with any legacy context. Translate at the edge; never let a legacy model leak inward |
| **Strangler Fig** | Incrementally route functionality to the new implementation behind a stable facade until the old one is dead |
| **Open Host Service + Published Language** | When many consumers depend on you and you cannot special-case them |
| **Separate Ways** | When integration costs exceed the value — duplicate deliberately and document why |
| **Bubble Context** | A small clean-model context created inside a legacy estate, protected by an ACL, as a beachhead |

---

## 6. Anti-patterns to flag

An agent encountering these should surface them explicitly rather than modelling around them.

- **Nanoservice** — a service too small to own an aggregate, coupled to siblings by synchronous calls. Diagnostic: an orchestrator fronting a fan of small, mechanism-named services.
- **Mechanism boundary** — services named for *how* rather than *what* (`*-batch`, `*-realtime`, one per protocol or downstream). Usually a policy variation inside one context, not a context boundary.
- **Entity service** — a service per database table (`customer-service`, `order-service`) with no behavior. Data-oriented, not domain-oriented.
- **Shared database** — two contexts writing the same tables. The boundary does not exist, whatever the deployment diagram says.
- **Anaemic domain model** — see §2.2.
- **Ubiquitous language drift** — the same word meaning different things inside one claimed context. Either the context is really two, or the language needs reconciling.
- **Distributed monolith** — services that must be deployed together. Worse than a monolith: same coupling, added network failure modes.
- **Big Ball of Mud** — a legitimate context-map entry. Naming it honestly is better than pretending it has a model.

---

## 7. Canonical sources

**Foundational**

- Eric Evans, *Domain-Driven Design: Tackling Complexity in the Heart of Software* (2003) — the origin text
- Vaughn Vernon, *Implementing Domain-Driven Design* (2013) and *Domain-Driven Design Distilled* (2016)
- [Effective Aggregate Design, Parts I–III — Vaughn Vernon](https://www.dddcommunity.org/library/vernon_2011/) — the source of §2.1. Short, free, and the single most useful text for Tactical Design

**Practitioner tooling** — [DDD Crew](https://github.com/ddd-crew), free and CC-licensed

- [Bounded Context Canvas](https://github.com/ddd-crew/bounded-context-canvas)
- [Aggregate Design Canvas](https://github.com/ddd-crew/aggregate-design-canvas)
- [Context Mapping](https://github.com/ddd-crew/context-mapping)
- [DDD Starter Modelling Process](https://github.com/ddd-crew/ddd-starter-modelling-process)
- [Domain Message Flow Modelling](https://github.com/ddd-crew/domain-message-flow-modelling)
- [Free DDD Learning Resources](https://github.com/ddd-crew/free-ddd-learning-resources)

**Modelling techniques**

- [EventStorming](https://www.eventstorming.com/) — Alberto Brandolini
- [Domain Storytelling](https://domainstorytelling.org/) — Hofer & Schwentner
- [Event Modeling](https://eventmodeling.org/) — Adam Dymitruk
- [Bounded Context Canvas v3](https://medium.com/nick-tune-tech-strategy-blog/bounded-context-canvas-v2-simplifications-and-additions-229ed35f825f) — Nick Tune

**Reference**

- [BoundedContext](https://martinfowler.com/bliki/BoundedContext.html), [UbiquitousLanguage](https://martinfowler.com/bliki/UbiquitousLanguage.html), [StranglerFigApplication](https://martinfowler.com/bliki/StranglerFigApplication.html) — Martin Fowler
- *Team Topologies* — Skelton & Pais, for the boundary/team-alignment relationship

**Tooling**

- [Contexture](https://github.com/trustbit/Contexture) — Bounded Context Canvas wizard; ContextRover exports to it
