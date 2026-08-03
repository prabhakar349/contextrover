<picture>
  <source media="(prefers-color-scheme: dark)" srcset="assets/logo-dark.svg">
  <img src="assets/logo.svg" alt="" width="96">
</picture>

# contextrover

**Domain-Driven Modernization (DDM):** spec-driven development where the spec is discovered, not declared.

ContextRover is a CLI-agent plugin that re-decomposes N existing services into M bounded-context-aligned services with **no unadjudicated behavioral change**, while serving both legacy and new interface surfaces at once. It supplies the stage that spec-driven development lacks — recovering an authoritative specification from a system that already works — and links every downstream artifact back to that evidence with a single traceability spine: `behavior → context → service(s) → surface → spec clause → characterization test → task → rollout check → retirement entry`.

**What it is not:** a code generator for target services. ContextRover produces **evidence, specs, and verification harnesses** — implementation happens through ordinary spec-driven development downstream, using whatever tooling your team already uses. It is not organization-specific (zero internal content ships in this repository), and it is not a replacement for [GitHub Spec Kit](https://github.com/github/spec-kit) — it supplies the stage Spec Kit lacks (evidence extraction) and hands off cleanly to conventional SDD after Stage 5.

Do not say "zero behavioral change." Say **"no unadjudicated behavioral change"** — every difference between old and new is either absent, or recorded with a named human owner and a rationale. The first claim is false the moment a difference is deliberately preserved as policy; the second survives audit.

## Relationship to Contexture

[Contexture](https://github.com/trustbit/Contexture) (trustbit, MIT) is a Bounded Context Canvas wizard for capturing and visualizing a target context model — it documents *where you want to be*. ContextRover does the archaeology and delivery to *get there*. The two are complementary, not competing.

## The nine stages

| # | Stage | Scope | Mode | Approver | Gate (script) |
|---|---|---|---|---|---|
| 0 | Engagement Intake | Engagement | Conversational, human-led | Program lead | `validate-artifacts.py --stage 0` |
| 1 | Domain Discovery | Engagement | Unattended Consensus Run | Tech lead | `validate-artifacts.py` / `trace-lint.py --stage 1` |
| 2 | Strategic Design | Engagement | Human-led, agent-prepared | Boundary approver (human) | `trace-lint.py --stage 2` |
| 3 | Solution Outline | Per Slice | Agent-drafted, reviewed | Product + tech lead | `trace-lint.py --stage 3` |
| 4 | Delivery Roadmap | Engagement | Agent-drafted, human-shaped | Leadership | `trace-lint.py --stage 4` |
| 5 | Tactical Design | Per Slice, JIT | Human-led, agent-prepared | Architecture review | `trace-lint.py --stage 5` |
| 6 | Verification Design | Per Slice | Adversarial, agent-heavy | QA / SRE | `trace-lint.py --stage 6`, `run-fitness.py` |
| 7 | Execution | Per Slice | Dispatched, harness-gated | Code review | harness runner, `run-fitness.py` |
| 8 | Transition | Per Modeled Context | Human-gated | Change management + sunset authority | `status-report.py` |

Stages 0–2 and 4 run once, at Engagement level. Stages 3, 5, 6, 7 repeat per Slice — Tactical Design (5) is deliberately just-in-time, not designed up front for every Slice. Stage 8 runs per Modeled Context, once every Slice in that Context reaches `Accepted`, because the Context — not the Slice — is the deployable boundary. The Consumer Migration Workstream runs cross-cutting and in parallel, starting once Stage 5 publishes new contracts; it never gates Stages 6–8.

**Every gate is machine-checkable.** Where a criterion genuinely requires human judgment (a boundary decision, a divergence classification), the gate is that a signed, schema-valid record of that judgment exists — not that the judgment was correct. Full contracts for every stage are in `07-stages.md`; the ubiquitous language they use is normative in `09-glossary.md`.

## Quickstart

1. **Install the plugin.** From the repository you want to modernize, open Claude Code and register this repository as a plugin source, then install it:

   ```
   /plugin marketplace add <path-or-git-url-to-this-repository>
   /plugin install contextrover@<marketplace-name>
   ```

   (Substitute whatever local path or git URL you cloned this repository to, and the marketplace name you gave it — see Claude Code's own plugin documentation for the exact marketplace-registration step in your environment.) Verify it loaded with `/rover-status` — it should report "Stage 0: not-started" with no errors.
2. **Write your Engagement Charter.** `charter.md` is gitignored and never ships — it carries your organization's standards, compliance baselines, and approval matrix, none of which belongs in a public repository. Run:

   ```
   /rover-init
   ```

   On the very first run, `/rover-init` also asks for the absolute filesystem path where this plugin is installed and records it in `.contextrover/state.json` as `plugin_root` — Claude Code doesn't expose an equivalent of `${CLAUDE_PLUGIN_ROOT}` to command or agent instructions the way it does to hooks, so every later command resolves the plugin's own `schemas/`, `packs/`, `knowledge/`, and scripts from this recorded path rather than a bare relative one. This happens once per engagement.

   If `charter.md` doesn't exist, `/rover-init` copies `charter.template.md` to `charter.md` and stops with instructions. Fill in every placeholder, then re-run `/rover-init`.
3. **Complete Stage 0 intake.** `/rover-init` walks a six-section conversational interview (estate, evidence sources, constraints, integrations, governance, delivery capacity), probing which MCP connectors are actually available *before* asking any configuration question for them. It finishes by initializing `.contextrover/` as its own git repository and printing which Stage 1 agents will run, which are disabled and why, and your highest-severity unresolved risks.
4. **Run Stage 1 Domain Discovery:**

   ```
   /rover-discover
   ```

   This runs unattended — nine read-only agents, three independent passes with varying framing, zero approval prompts — and produces the Interface Inventory (sync and async), Behavior Inventory, Divergence Register, change-coupling analysis, call-sequence analysis, and a Redaction Policy assessment per interface, all under `.contextrover/inventory/`.
5. **Check where you stand at any time**, with no network access, from any stage:

   ```
   /rover-status
   ```

Stages 2 through 8 follow the same pattern — `/rover-model`, `/rover-outline`, `/rover-roadmap`, `/rover-design <slice-id>`, `/rover-verify <slice-id>`, `/rover-execute <slice-id>`, `/rover-transition <context-id>` — each checking its prerequisites, loading the charter, running its gate scripts, and committing `.contextrover/` on success. `/rover-migrate` drives the parallel Consumer Migration Workstream. `/rover-project <adapter>` explicitly projects local artifacts to a connected external system (issue tracker, wiki, or version control) — projection is never automatic.

## The framework/charter split, and why it matters

Two documents are easy to confuse and must not be:

- **`00-constitution.md`** (this repository) — principles governing how *the plugin itself* is built. Public, generic, ships with every install.
- **`charter.md`** (your repository, gitignored) — your organization's standards, compliance interpretations, naming conventions, and approval matrix. Private, specific to your engagement, **never committed**.

This split exists because the repository is public and domain-agnostic by design (no internal standards, platform names, service inventories, or endpoint lists may ever appear here) — and because a missing charter must fail loudly, not silently default. `/rover-init` refuses to proceed past a missing or placeholder-only charter.

## The nested `.git` — this will surprise you

`/rover-init` runs `git init` **inside** `.contextrover/`. This is deliberate: `.contextrover/` is its own git repository, separate from your source estate's history, so evidence history never entangles with application history. It gives you full history of how understanding evolved (a Behavior record's `git blame` shows which pass and which Adjudication produced it), diffable artifacts between gates, and recoverable state after a bad stage re-run. Your source repository's own `.gitignore` should ignore `.contextrover/` as a directory (it is a nested repository, not a submodule) — `/rover-init` sets this up for you, but if you ever see two `.git` directories in one tree and wonder why, this is why.

## Extension points

v1 ships **brownfield only** — the Characterization oracle, where the existing system is the oracle for correctness. `12-extension-seams.md` documents what's deliberately deferred (a Specification oracle for greenfield work, observability and chat connectors, LSP-based discovery, a Contexture export adapter) and the seams already built into v1 so none of it requires rework later — for example, every Slice already carries a required `oracle_strategy` field, even though v1 only accepts one value for it.

## Credits

- **[Contexture](https://github.com/trustbit/Contexture)** (trustbit, MIT) — the Bounded Context Canvas wizard this framework exports to; see "Relationship to Contexture" above.
- **`knowledge/ddd-reference.md`** — canonical Domain-Driven Design distilled into operational rules: Eric Evans' and Vaughn Vernon's foundational work, the [DDD Crew](https://github.com/ddd-crew)'s free, CC-licensed practitioner tooling (Bounded Context Canvas, Aggregate Design Canvas, Context Mapping), and Martin Fowler's reference material. Full citations at the end of that file.
- **`knowledge/modernization-knowledge-store.md`** — curated agentic-modernization prior art, primarily sourced from Markus Harrer's [awesome-agentic-software-modernization](https://github.com/feststelltaste/awesome-agentic-software-modernization) (CC BY 4.0), plus independently gathered material. Full citations at the end of that file.

## License

MIT. See `LICENSE`.
