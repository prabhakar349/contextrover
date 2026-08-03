<!--
  ENGAGEMENT CHARTER — TEMPLATE

  Copy this file to `charter.md` (already in .gitignore — never commit the
  completed file; it contains your organization's standards, compliance
  interpretations, and internal naming, none of which belongs in a public
  repository — Constitution C4). If `charter.md` is missing, `/rover-init`
  stops and tells you to create it from this template; it will not proceed
  on a placeholder.

  Every value below is a placeholder in an HTML comment or a bracketed
  [ ... ] token. Replace every one of them. `/rover-init` checks for
  leftover placeholder tokens and fails actionably if it finds any —
  it will not silently default a missing standard (Constitution C4).
-->

# Engagement Charter

## Architecture standards

<!-- e.g. required patterns, forbidden patterns, technology allowlist -->
[ Describe your organization's architecture standards that any target design must conform to. ]

## Security and compliance baselines

<!-- e.g. which regulatory frameworks apply, data classification rules, required controls -->
[ Describe the security and compliance baselines this engagement must satisfy. ]

## Observability requirements

<!-- e.g. required logging format, mandated metrics, tracing standard -->
[ Describe what "day-zero observability" means for this organization — what must be provisioned before any Slice ships. ]

## Naming conventions

<!-- e.g. service naming, repository naming, event/topic naming -->
[ Describe naming conventions the target architecture must follow. ]

## Approval matrix

<!-- Who signs which gate. This feeds intake Section E (06-intake.md). -->
[ Name who approves: boundary decisions (Stage 2), the roadmap (Stage 4),
  architecture review (Stage 5), decommissioning (Stage 8). ]

## Agreed success metric

<!--
  The default and recommended metric is:
  "zero boundaries that do not correspond to a bounded context"
  — not a target service count. If your organization has mandated a
  specific service count instead, name it here AND record who mandated
  it — 06-intake.md Section E (E1/E2) treats an un-reframed mandated count
  as a high-severity risk that should be resolved before Stage 2 produces
  a number that may contradict it.
-->
[ State the agreed success metric for this engagement. ]

## Sunset authority

<!--
  Who can mandate a legacy interface's retirement date. If this is left
  null, every legacy interface is effectively permanent in practice —
  06-intake.md Section E (E4) and the Consumer Migration Workstream gate
  both depend on this being answered.
-->
[ Name who holds sunset authority for this engagement. ]
