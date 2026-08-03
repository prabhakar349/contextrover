# The Narrative — how to explain Domain-Driven Modernization

Not part of the build. This is the sequence for explaining the method to engineers, architects, and executives — each of whom needs a different entry point into the same seven moves.

---

## The central claim

> **You can't go fast because you can't verify fast.**
>
> Every modernization program is throttled by the same thing: nobody can prove the new system does what the old one did. So every change gets a review meeting, every cutover gets a committee, and a six-week job takes nine months.
>
> Fix verification and speed is a by-product — not a risk you accepted.

This inverts the usual pitch. Most acceleration stories ask leadership to trade safety for speed. This one says the safety mechanism *is* the accelerator, because objective gates remove the human bottleneck that was never adding safety in the first place.

---

## The seven moves

### 1. Introspect — *the system tells you what it does*

Agents read every service exhaustively and produce an inventory of interfaces and behaviors, each with an ID and a citation. Multiple independent passes, from different vantage points, so coverage is measured rather than hoped for.

**The line:** "We stopped guessing what the system does. We asked it."

**Why it lands:** everyone in the room has been in a design review where the answer to "does it handle X?" was someone's recollection.

### 2. Agree — *humans decide the things only humans can decide*

Where services disagree about the same concept, that disagreement is surfaced, classified, and assigned to a named owner. Three outcomes only: model it as explicit policy, split it into separate contexts, or record it as a defect and fix it *later*.

**The line:** "The machine finds the disagreements. People resolve them. Once."

**Why it lands:** this is where the business discovers its own inconsistencies — usually for the first time. That artifact has value independent of the migration.

### 3. Lock — *pin behavior before anything moves*

Every behavior becomes an executable test against the *existing* system, at the protocol boundary. The old system becomes the specification. Tests are written before any code changes, because tests written afterward encode the new system's assumptions.

**The line:** "We wrote the tests against the system we're replacing, while it still worked."

**Why it lands:** it is the opposite of how these programs usually run, and the reason is obvious once stated.

### 4. Rebuild — *redraw the boundaries, with the oracle fixed*

Now the domain model is redrawn properly — bounded contexts, not mechanism or org chart. Agents do the volume work, continuously judged against a suite that cannot move. New contracts are designed from real observed call sequences, not imagined ones.

**The line:** "The target moved. The scoreboard didn't."

### 5. Prove — *conformity is measured, not asserted*

Coverage is one number: the percentage of catalogued behaviors with a passing test against the new system. Computable at any moment, by anyone. Architecture rules run in CI. No status meeting produces this number; the repository does.

**The line:** "Ask me how much of the old behavior we've *proven* we preserved. I have a number. Most programs have an opinion."

**Why it lands:** this is the executive hook. It converts a program that historically reports in adjectives into one that reports in arithmetic.

### 6. Move — *traffic shifts on evidence*

Shadow, then canary, then progressive — per bounded context, sequenced by blast radius. Every gate is a threshold, not a judgment. Old services decommission on objective criteria.

**The line:** "Nothing moved because someone felt ready."

### 7. Retire — *and actually finish*

Consumers migrate to the new contracts at their own pace, on a separate track that never blocks the convergence. Every legacy interface has a named sunset authority and a date. Zero traffic for N days is the retirement gate.

**The line:** "Most migrations never end because nobody owns the last mile. We named an owner for every interface on day one."

**Why it lands:** every senior person in the room has seen a "temporary" compatibility layer outlive its authors.

---

## Framing by audience

| Audience | Lead with | The number that matters |
|---|---|---|
| **Executives** | Move 5 — verification as a measurable percentage | Behavior conformity %, and the count of interfaces with no sunset owner |
| **Architects** | Moves 2 and 4 — boundaries corrected, not just fewer deployables | Services that fail the anti-nanoservice test today |
| **Engineers** | Moves 1 and 3 — the tedious part is automated, the risky part is pinned | Hours not spent reading eleven codebases by hand |
| **Risk / compliance** | Moves 3, 5, 6 — evidence, audit trail, objective gates | Append-only gate log with artifact hashes |
| **Consumer teams** | Move 7 — nothing breaks, migrate when ready | Zero required changes at cutover |

---

## The three objections, and the honest answers

**"AI wrote our architecture?"**
No. Agents extracted evidence and proposed options. Every boundary decision has a named human owner and a written rationale. Published research on automated DDD finds exactly this limitation — models produce theoretically clean boundaries while missing practical coupling and operational cost — which is why the method feeds them empirical coupling data and keeps the decision human.

**"How do we know it didn't miss something?"**
We can't prove a negative, and we don't claim to. What we report is the agreement rate across independent extraction passes, and every behavior found by only one pass is inspected by a person. That is a measured coverage estimate rather than an assurance — which is more than the alternative offers.

**"What if the tests are wrong?"**
The tests are generated from the running system's actual responses, not from anyone's understanding of it. A wrong test means the old system did something surprising — which is itself a finding worth having, and it surfaces before cutover rather than after.

---

## What not to say

- Don't promise a service count. Promise zero boundaries that don't correspond to a bounded context. Numbers commit you to a decision the analysis hasn't made yet.
- Don't call it a rewrite. It is behavior-preserving by construction, and "rewrite" triggers everyone's worst memory.
- Don't sell the speed first. Sell the verification; let speed be the consequence. Leading with speed invites the question "what are you cutting?"
