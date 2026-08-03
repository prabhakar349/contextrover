# Modernization Knowledge Store

Curated prior art for building an agentic, DDD-conformant service re-decomposition tool. Organized **by the phase it informs**, not by source — each entry states what to take and what to leave.

Primary source: [awesome-agentic-software-modernization](https://github.com/feststelltaste/awesome-agentic-software-modernization) (Markus Harrer, CC BY 4.0), plus independently gathered material.

**Status legend:** ⭐ = changes the design · ✅ = confirms a design decision · 📖 = background

---

## 0. The four findings that changed the design

### ⭐ CodeConcise — knowledge graph over code, not just a file inventory

[Thoughtworks / Martin Fowler site (Sept 2024)](https://martinfowler.com/articles/legacy-modernization-gen-ai.html) — Ferri, Coggrave, Sheth.

Combines LLMs with **knowledge graphs derived from code syntax trees**, used for reverse-engineering requirements, system comprehension, capability mapping, and technology translation.

**Take:** the evidence layer should be a **graph**, not a folder of JSON documents. The traceability spine already *is* a graph — service → interface → behavior → context → test → rollout. Storing it as one makes lint queries, impact analysis, and reporting fall out naturally instead of requiring bespoke code each time.

**Leave:** the graph-database dependency. A JSONL node/edge store queried with the standard library is sufficient at this scale and keeps the tool installable anywhere.

### ⭐ Serena — LSP-based semantic code tools across 30+ languages

[github.com/oraios/serena](https://github.com/oraios/serena)

Turns an LLM into an agent with IDE-grade capability: symbol discovery, reference finding, semantic editing, via Language Server Protocol.

**Take:** this substantially solves the polyglot problem. Grep patterns per framework per language are brittle and endless; LSP gives symbol-level truth across 30+ languages from one interface. Recommend Serena as an **optional discovery evidence source** — when present, extraction quality rises sharply; when absent, fall back to pattern-based pack discovery.

**Design consequence:** language packs should declare *both* a pattern-based path and an LSP-based path, and prefer LSP when available.

### ⭐ Snapshot testing for cross-language functional equivalence

Calvin Smith, [Refactoring COBOL to Java with Agentic AI (Jan 2026)](https://www.youtube.com/watch?v=4LUtguF160A) — OpenHands.

Uses an **iterative refinement loop with Engineer and Critic agents** plus **snapshot testing to prove functional equivalence across languages**.

**Take:** independent field validation of two core decisions — characterization at the protocol boundary survives a language change, and adversarial Engineer/Critic pairing is the right shape for generation phases. This is the closest existing work to what we are building, and it worked.

**Also take:** the vocabulary. "Functional equivalence across the transformation" is a clearer phrase for executives than "behavior preservation."

### ⭐ Event Modeling + AI for legacy analysis

Martin Dilger, [Using Event Modeling and AI for Legacy System Analysis (Oct 2025)](https://www.youtube.com/watch?v=xKepFagd-kc)

AI analyzes legacy codebases and **auto-generates Event Models that domain experts can then discuss**. Live demo on Spring PetClinic; scales to larger systems.

**Take:** this is precisely the Phase 2 posture — the agent *prepares* the workshop artifact, humans *decide*. It confirms that generating a first-draft event model from code is feasible today, which is the expensive part of running EventStorming on an estate nobody fully understands.

---

## 1. Phase 1 — Discover / Characterize (software archaeology)

### 📖 The discipline has a name

Markus Harrer, [Getting to Know Your Legacy System with AI-Driven Software Archeology (July 2025)](https://www.youtube.com/live/vBpJFUCJNKw) · [slides](https://speakerdeck.com/feststelltaste/getting-to-know-your-legacy-system-with-ai-driven-software-archeology-wearedevelopers-world-congress-2025)

Data-driven approaches to understanding legacy systems. Use **"software archaeology"** as the name for Phase 1 in user-facing material — it is established, evocative, and immediately understood.

### ✅ Confidence scoring and iterative extraction

Markus Harrer, [LLM-assisted Abbreviation Mining for Legacy Systems (Nov 2024)](https://www.innoq.com/en/blog/2024/11/llm-assisted-abbreviation-mining/)

Claude 3.5 Sonnet deciphering abbreviations in a COBOL banking system: iterative extraction, **expansion with confidence scores**, concept-to-component mapping, 99% file coverage.

**Take:** confidence scores on every extracted item, and iteration to convergence rather than a single pass. Both already in the behavior schema — this validates them and gives a coverage benchmark to aim at.

**Also take:** abbreviation and jargon mining is a genuinely useful Phase 1 sub-task in any old estate, and feeds directly into the ubiquitous language artifact in Phase 2.

### 📖 Context engineering for legacy comprehension

Böckeler & Thiagarajan, [Context Engineering — Tackling Legacy Systems with Generative AI (Thoughtworks podcast, Aug 2025)](https://www.youtube.com/watch?v=Uhs8o4qPvd0)

On reverse-engineering legacy systems through deliberate context construction. Reinforces that *what you put in front of the model* dominates outcome quality — which is the argument for framing-variation ensembles over model-tier variation.

### 📖 Software analytics as the quantitative half

Markus Harrer, [Software Analytics going crAIzy! (Sept 2025)](https://www.innoq.com/en/blog/2025/09/software-analytics-going-craizy/)

Two-phase approach: identify problems through data analysis, then apply AI-driven solutions. Supports change-coupling mining as first-class boundary evidence rather than a nice-to-have.

---

## 2. Phase 2 — Domain modeling

### ✅ LLMs propose, humans decide

*Automating Domain-Driven Design: Experience with a Prompting Framework* — [arXiv 2603.26244](https://arxiv.org/pdf/2603.26244)

Finds LLMs identify **theoretically valid boundaries but miss practical dependencies, coupling, and operational overhead** that human architects weigh.

**Take:** the single strongest citation for keeping boundary decisions human-adjudicated, and for feeding empirical change-coupling data into the proposal step. Quote it directly when someone asks why the tool doesn't just decide.

### 📖 Grounding agents in structured knowledge

Tomaž Bratanič, [RAG on a Knowledge Graph (Neo4j, Aug 2025)](https://neo4j.com/blog/developer/rag-tutorial/)

Knowledge graphs + vector search for grounding LLM agents in reliable structured knowledge.

**Take:** the retrieval pattern — when an agent asks "what else touches this concept?", answer from the graph rather than from a fresh grep. Cheaper, more complete, and reproducible.

---

## 3. Phases 3–5 — Specify, verify, implement

### ✅ Engineer / Critic adversarial loop

Calvin Smith (above) — validated in a real COBOL→Java migration.

Confirms the `spec-critic` and `test-adversary` agents. The critic is not a review step bolted on; it is half the loop.

### 📖 The author of characterization testing on working with AI

Michael Feathers, [AI Assisted Programming (2025, in progress)](https://leanpub.com/ai-assisted-programming)

Feathers coined "characterization test." His current work on AI collaboration, TDD, and iterative refinement is the most directly relevant single author for this framework's verification layer.

### 📖 Brownfield agentic framework

[BMad-Method Brownfield Guide (Sept 2025)](https://github.com/bmad-code-org/BMAD-METHOD/blob/main/src/modules/bmm/docs/brownfield-guide.md)

Open-source framework for AI-driven development with modular agent components, including explicit brownfield guidance.

**Take:** compare its agent decomposition against ours before finalizing the agent roster. Prior art on *which* agents a brownfield workflow actually needs.

### 📖 Specs as the primary artifact

Andrew Crookston, [The next programming superpower is specs, documentation and orchestrating agentic AI (Oct 2025)](https://andrewcrookston.com/articles/agentic-coding.html)

Argues the critical skill shifts from writing code to writing specifications — documentation quality becomes the productivity differentiator. Useful framing material for the narrative document.

---

## 4. Program-level and executive material

### 📖 Anthropic Code Modernization Playbook (Sept 2025)

[PDF](https://resources.anthropic.com/hubfs/Code%20Modernization%20Playbook.pdf)

Migration strategies, prompt engineering, tool-selection evaluation frameworks, ROI analysis, implementation timelines, team readiness assessment.

**Take:** ROI framing and readiness assessment for the intake interview and the executive narrative. Complementary rather than competing — it is a playbook, not a tool.

### 📖 McKinsey LegacyX

Bawcom & Santos, [Accelerate app modernization with generative AI (April 2024)](https://www.youtube.com/watch?v=zddFQLHdP50)

Automating discovery and documentation, target-state code generation, unit and functional testing. Useful for the "large consultancies are doing this too" slide; light on verifiable method.

### 📖 Field experience and limitations

Fabrice Bernhard, [AI accelerated legacy modernisation (June 2025)](https://www.youtube.com/watch?v=Vbm20F-q-ak) — concrete experiences and honest limitations, framed around retiring engineers taking system knowledge with them. Good source for the risk framing in an executive conversation.

Nicky Pike & Dave Ahr, [AI-Assisted Legacy Code Modernization: A Developer's Guide (June 2025)](https://coder.com/blog/ai-assisted-legacy-code-modernization-a-developer-s-guide) — where AI delivers genuine value versus where it doesn't.

Ray Myers, [Code Mending in the AI age (Craft 2024)](https://www.youtube.com/watch?v=-r1yB6wCRP8) — on "Menders" as a distinct engineering identity.

---

## 5. Adjacent tools worth knowing

| Tool | What it does | Relationship to us |
|---|---|---|
| [Serena](https://github.com/oraios/serena) | LSP-based semantic code tools, 30+ languages | **Optional evidence source.** Adopt as a pack-level integration |
| CodeConcise | LLM + code knowledge graph (Thoughtworks, not open) | Architectural precedent for the graph store |
| [CodeMender](https://deepmind.google/discover/blog/introducing-codemender-an-ai-agent-for-code-security/) | Google agent for security patching at scale | Different problem; useful proof that agents operate on multi-million-line codebases |
| OpenHands | Agent platform used in the COBOL→Java work | Validated the Engineer/Critic + snapshot pattern |
| Diffblue / Qodo Cover | Automatic **unit** test generation | **Wrong layer for us.** Pins internals, which we redraw by design |

---

## 6. Gaps this store confirms

Nothing found in the corpus does all of the following together, which is the space the tool occupies:

1. **Re-decomposition**, not decomposition — the existing work overwhelmingly targets monolith→microservices or language migration. Distributed estate → corrected boundaries is barely addressed.
2. **A traceability spine** linking evidence → spec → test → rollout → retirement with a computable completion metric.
3. **Dual-surface delivery** — legacy and new contracts served simultaneously, with convergence decoupled from consumer migration.
4. **Async interfaces as first-class contracts.** Almost every source is HTTP- or batch-oriented. Event streams with ordering, partitioning and delivery semantics are essentially unaddressed, and they are the hardest part.

Item 4 is the widest gap in the published field and the strongest claim to novelty.

---

## 7. Sources to revisit

Not yet incorporated; worth a pass before v1.0:

- [Awesome Legacy Systems](https://github.com/feststelltaste/awesome-legacy-systems)
- [Awesome Software Analytics](https://github.com/feststelltaste/awesome-software-analytics)
- [ai-agents-from-scratch](https://github.com/pguso/ai-agents-from-scratch/) — agent micro-patterns, ReAct, persistent memory
- [Harrer's micro-patterns gist](https://gist.github.com/feststelltaste/6e488f9d0db7fd7cc5b4b9d984d3ed05) — early collection of agent micro-patterns for modernization
- Nick Tune, [Reverse Engineering Your Software Architecture with Claude Code](https://medium.com/nick-tune-tech-strategy-blog/reverse-engineering-your-software-architecture-with-claude-code-to-help-claude-code-1746a7b941bc)
