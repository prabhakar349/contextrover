# Artifact Schemas — contextrover

JSON Schema draft 2020-12. Every artifact the plugin writes must validate against one of these. Markdown views are generated from these documents, never authored alongside them (Constitution C7).

Common conventions:

- `id` patterns are fixed by decision D2 and never renumbered (REQ-31).
- Every artifact carries `evidence[]` — where the claim came from. An assertion without evidence is a defect.
- `confidence` is `high` | `medium` | `low` | `unknown`. `unknown` is a valid, expected value and must carry a `reason` (REQ-09, C10).

---

## behavior.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "behavior.schema.json",
  "title": "Behavior Record",
  "type": "object",
  "required": ["id", "summary", "source_services", "evidence", "confidence"],
  "properties": {
    "id":            { "type": "string", "pattern": "^BHV-[0-9]{4}$" },
    "summary":       { "type": "string", "minLength": 10 },
    "detail":        { "type": "string" },
    "source_services": { "type": "array", "items": { "type": "string" }, "minItems": 1 },
    "interfaces":    { "type": "array", "items": { "type": "string", "pattern": "^IFC-(SYNC|ASYNC)-[0-9]{4}$" } },
    "kind":          { "enum": ["validation", "calculation", "routing", "state-transition", "error-mapping", "side-effect", "emission", "other"] },
    "failure_path":  { "type": "boolean", "description": "True if this describes failure, timeout or partial-completion behavior. Under-represented by default; see 01-spec DR1." },
    "evidence":      { "$ref": "#/$defs/evidence" },
    "confidence":    { "enum": ["high", "medium", "low", "unknown"] },
    "reason":        { "type": "string", "description": "Required when confidence is unknown" },
    "agreement":     { "type": "object", "properties": {
                         "found_by": { "type": "array", "items": { "type": "string" } },
                         "k":        { "type": "integer" },
                         "score":    { "type": "number", "minimum": 0, "maximum": 1 } } },
    "context":       { "type": "string", "pattern": "^CTX-[0-9]{4}$" },
    "target_services": { "type": "array", "items": { "type": "string" } },
    "spec_clauses":  { "type": "array", "items": { "type": "string" } },
    "tests":         { "type": "array", "items": { "type": "string" } },
    "status":        { "enum": ["confirmed", "unconfirmed"], "default": "confirmed",
                       "description": "unconfirmed = present in an earlier run, not found in the latest. Never auto-deleted (REQ-31a)." },
    "last_seen_run": { "type": "integer" }
  },
  "$defs": {
    "evidence": {
      "type": "array", "minItems": 1,
      "items": {
        "type": "object",
        "required": ["source", "locator"],
        "properties": {
          "source":  { "enum": ["code", "test", "doc", "traffic", "stream-metadata", "commit-history", "config"] },
          "locator": { "type": "string", "description": "file:line, topic name, or query" },
          "excerpt": { "type": "string" }
        }
      }
    }
  }
}
```

---

## interface.schema.json

One record per interface. `async` records carry the fields that make event contracts genuinely comparable — payload equality is not sufficient (REQ-02).

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "interface.schema.json",
  "title": "Interface Record",
  "type": "object",
  "required": ["id", "kind", "name", "owning_service", "evidence"],
  "properties": {
    "id":   { "type": "string", "pattern": "^IFC-(SYNC|ASYNC)-[0-9]{4}$" },
    "kind": { "enum": ["sync", "async-published", "async-consumed"] },
    "name": { "type": "string" },
    "owning_service": { "type": "string" },
    "protocol": { "enum": ["http", "grpc", "kafka", "sqs", "pubsub", "amqp", "other"] },

    "sync": {
      "type": "object",
      "properties": {
        "method": { "type": "string" },
        "path":   { "type": "string" },
        "request_schema":  { "type": "string" },
        "response_schema": { "type": "string" },
        "status_codes":    { "type": "array", "items": { "type": "integer" } }
      }
    },

    "async": {
      "type": "object",
      "properties": {
        "topic":              { "type": "string" },
        "payload_schema":     { "type": "string" },
        "schema_registry_id": { "type": "string" },
        "partition_key":      { "type": "string" },
        "ordering_guarantee": { "enum": ["none", "per-partition", "global", "unknown"] },
        "delivery":           { "enum": ["at-most-once", "at-least-once", "exactly-once", "unknown"] },
        "idempotency_key":    { "type": "string" },
        "retry_policy":       { "type": "string" },
        "dlq":                { "type": "string" },
        "retention":          { "type": "string" },
        "consumer_groups":    { "type": "array", "items": { "type": "string" } }
      }
    },

    "consumers": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["identifier", "evidence_source", "confidence"],
        "properties": {
          "identifier":      { "type": "string" },
          "evidence_source": { "enum": ["access-log", "consumer-group", "schema-registry", "code-reference", "documentation", "declared", "none"] },
          "confidence":      { "enum": ["high", "medium", "low", "unknown"] },
          "last_seen":       { "type": "string", "format": "date" }
        }
      }
    },
    "consumers_complete": {
      "type": "boolean",
      "description": "False means unknown consumers may exist. For async interfaces this defaults to false unless registry AND consumer-group evidence are both present."
    },
    "evidence": { "$ref": "behavior.schema.json#/$defs/evidence" }
  }
}
```

**Note on `consumers_complete`:** it defaults to `false` for async interfaces by design. Claiming a complete consumer list without both registry and consumer-group evidence is the single most dangerous false confidence in the whole method.

---

## divergence.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "divergence.schema.json",
  "title": "Divergence Record",
  "type": "object",
  "required": ["id", "concept", "variants", "evidence"],
  "properties": {
    "id":      { "type": "string", "pattern": "^DVG-[0-9]{4}$" },
    "concept": { "type": "string", "description": "The single concept the services disagree about" },
    "variants": {
      "type": "array", "minItems": 2,
      "items": {
        "type": "object",
        "required": ["service", "behavior_id", "description"],
        "properties": {
          "service":     { "type": "string" },
          "behavior_id": { "type": "string", "pattern": "^BHV-[0-9]{4}$" },
          "description": { "type": "string" }
        }
      }
    },
    "classification": {
      "enum": ["unclassified", "policy", "false-cognate", "defect"],
      "description": "policy = model as explicit domain variation; false-cognate = things that look like one concept but belong to different bounded contexts; defect = preserve, log, fix separately AFTER migration"
    },
    "driving_dimension": { "type": "string", "description": "What actually varies: channel, product, tenant, mechanism" },
    "decision_owner":    { "type": "string" },
    "decided_at":        { "type": "string", "format": "date-time" },
    "rationale":         { "type": "string" },
    "projection":        { "type": "object", "properties": {
                             "adapter":     { "type": "string" },
                             "external_id": { "type": "string" },
                             "status":      { "enum": ["pending", "projected", "failed"] } } },
    "evidence": { "$ref": "behavior.schema.json#/$defs/evidence" }
  }
}
```

A divergence left `unclassified` past Stage 2 is a gate failure. Each one needs a named human owner — which is exactly why divergences project to issue-tracker items (REQ-46).

---

## adjudication.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "adjudication.schema.json",
  "title": "Adjudication Record",
  "type": "object",
  "required": ["id", "stage", "k", "candidates", "decided_by", "decided_at"],
  "properties": {
    "id":    { "type": "string", "pattern": "^ADJ-[0-9]{4}$" },
    "stage": { "type": "integer", "minimum": 0, "maximum": 8 },
    "k":     { "type": "integer", "minimum": 1 },
    "framings": { "type": "array", "items": { "type": "string" } },
    "candidates": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["candidate_id", "found_by", "decision"],
        "properties": {
          "candidate_id": { "type": "string" },
          "found_by":     { "type": "array", "items": { "type": "string" } },
          "partition":    { "enum": ["all", "some", "one"] },
          "decision":     { "enum": ["accept", "reject", "triage"] },
          "rationale":    { "type": "string" }
        }
      }
    },
    "kind":       { "enum": ["consensus-run", "adjudication"],
                    "description": "consensus-run = mechanical, agent-produced, re-executable. adjudication = an accountable human decision, only supersedable." },
    "decided_by": { "type": "string",
                    "description": "When kind == 'adjudication' this MUST be a human identity. An agent name here is a schema violation, not a shortcut — see 09-glossary.md §2." },
    "decided_at": { "type": "string", "format": "date-time" },
    "agreement_rate": { "type": "number", "minimum": 0, "maximum": 1 }
  }
}
```

---

## retirement.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "retirement.schema.json",
  "title": "Legacy Surface Retirement Entry",
  "type": "object",
  "required": ["interface_id", "status"],
  "properties": {
    "interface_id":     { "type": "string", "pattern": "^IFC-(SYNC|ASYNC)-[0-9]{4}$" },
    "known_consumers":  { "type": "array", "items": { "type": "string" } },
    "status":           { "enum": ["active", "deprecated", "zero-traffic", "retired"] },
    "sunset_date":      { "type": ["string", "null"], "format": "date" },
    "sunset_authority": { "type": ["string", "null"], "description": "Who can mandate this date. Null means the interface is effectively permanent." },
    "last_traffic":     { "type": ["string", "null"], "format": "date-time" },
    "zero_traffic_days": { "type": "integer" },
    "migration_guide":  { "type": ["string", "null"] }
  }
}
```

`sunset_authority: null` is the signal that an interface is permanent in practice. The status report must surface the count of such interfaces prominently — it is the leading indicator that the Consumer Migration Stream will never finish.

---

## state.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "state.schema.json",
  "title": "Stage State Ledger",
  "type": "object",
  "required": ["version", "stages"],
  "properties": {
    "version": { "type": "string" },
    "target":  { "type": "object", "properties": {
                   "services":  { "type": "array", "items": { "type": "string" } },
                   "languages": { "type": "array", "items": { "enum": ["java", "go", "python", "other"] } } } },
    "stages": {
      "type": "object",
      "patternProperties": {
        "^[0-8]$": {
          "type": "object",
          "required": ["status"],
          "properties": {
            "status":       { "enum": ["not-started", "in-progress", "gate-failed", "complete"] },
            "started_at":   { "type": "string", "format": "date-time" },
            "completed_at": { "type": "string", "format": "date-time" },
            "operator":     { "type": "string" },
            "gate_result":  { "type": "object", "properties": {
                                "passed":   { "type": "boolean" },
                                "script":   { "type": "string" },
                                "exit_code":{ "type": "integer" },
                                "summary":  { "type": "string" } } },
            "artifacts":    { "type": "array", "items": { "type": "string" } }
          }
        }
      }
    },
    "counters": {
      "type": "object",
      "description": "Last-issued sequence number per ID prefix. Guarantees stable IDs across re-runs (REQ-31).",
      "properties": {
        "BHV": { "type": "integer" }, "IFC_SYNC": { "type": "integer" },
        "SLC": { "type": "integer" }, "WS": { "type": "integer" },
        "IFC_ASYNC": { "type": "integer" }, "DVG": { "type": "integer" },
        "CTX": { "type": "integer" }, "ADJ": { "type": "integer" }
      }
    }
  }
}
```

---

## gates.jsonl

Append-only, one JSON object per line. Never rewritten — this is the audit trail (REQ-33).

```json
{"ts":"2026-08-01T12:00:00Z","stage":1,"script":"trace-lint.py","exit_code":0,"operator":"","summary":"...","artifact_hashes":{"behaviors.json":"sha256:..."}}
```

Artifact hashes make it possible to prove after the fact which version of the evidence a gate actually passed against.

---

# 7. Delivery schemas (Stages 3–8)

Same conventions as above. Every artifact under `.contextrover/` must validate against one of these; there are no exempt artifacts.

## slice.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "slice.schema.json",
  "title": "Slice",
  "type": "object",
  "required": ["id", "workstream", "oracle_strategy", "behaviors", "state"],
  "properties": {
    "id":             { "type": "string", "pattern": "^SLC-[0-9]{4}$" },
    "name":           { "type": "string" },
    "workstream":     { "type": "string", "pattern": "^WS-[0-9]{4}$" },
    "context":        { "type": ["string","null"], "pattern": "^CTX-[0-9]{4}$" },
    "oracle_strategy":{ "enum": ["characterization", "specification"],
                        "description": "SEAM S1.1 — v1 accepts only 'characterization'. Required, never optional." },
    "behaviors":      { "type": "array", "items": { "type": "string", "pattern": "^BHV-[0-9]{4}$" },
                        "description": "Non-empty when oracle_strategy is characterization. Left open for the specification oracle, where acceptance criteria carry the scope (seam S1.1)." },
    "use_cases":      { "type": "array", "items": { "type": "string" } },
    "state":          { "enum": ["Outlined","Designed","OracleFrozen","Building","Accepted"] },
    "harness_lock":   { "type": ["string","null"], "description": "sha256 of the frozen characterization suite" },
    "approvals":      { "type": "array", "items": { "$ref": "approval.schema.json" } }
  }
}
```

## workstream.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "workstream.schema.json",
  "title": "Workstream",
  "type": "object",
  "required": ["id", "kind", "state"],
  "properties": {
    "id":      { "type": "string", "pattern": "^WS-[0-9]{4}$" },
    "kind":    { "enum": ["context-scoped", "walking-skeleton", "consumer-migration"] },
    "context": { "type": ["string","null"], "pattern": "^CTX-[0-9]{4}$",
                 "description": "Null for cross-cutting workstreams — they belong to the Engagement" },
    "owner":   { "type": "string" },
    "state":   { "enum": ["Open","Active","Complete"] }
  }
}
```

## approval.schema.json

The C2 escape hatch made concrete. A gate criterion that cannot be scripted is satisfied by the existence of one of these.

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "approval.schema.json",
  "title": "Approval Record",
  "type": "object",
  "required": ["criterion", "artifact", "version_hash", "decided_by", "decided_at"],
  "properties": {
    "criterion":    { "type": "string", "description": "The exact gate criterion being attested" },
    "artifact":     { "type": "string" },
    "version_hash": { "type": "string", "description": "sha256 of the artifact at approval time. Approval voids if this changes." },
    "decided_by":   { "type": "string", "description": "Human identity. Never an agent name." },
    "decided_at":   { "type": "string", "format": "date-time" },
    "rationale":    { "type": "string" }
  }
}
```

## size.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "size.schema.json",
  "title": "Slice Size",
  "type": "object",
  "required": ["slice", "behaviors", "interfaces_sync", "interfaces_async"],
  "properties": {
    "slice":                   { "type": "string", "pattern": "^SLC-[0-9]{4}$" },
    "behaviors":               { "type": "integer", "minimum": 0 },
    "failure_path_behaviors":  { "type": "integer", "minimum": 0 },
    "interfaces_sync":         { "type": "integer", "minimum": 0 },
    "interfaces_async":        { "type": "integer", "minimum": 0 },
    "divergences_open":        { "type": "integer", "minimum": 0 },
    "consumers_affected":      { "type": "integer", "minimum": 0 },
    "data_migration_required": { "type": "boolean" }
  },
  "not": { "required": ["duration_days"] },
  "description": "Contains no dates. Dates are produced only in Stage 4."
}
```

## roadmap.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "roadmap.schema.json",
  "title": "Delivery Roadmap",
  "type": "object",
  "required": ["version_hash", "increments", "capacity", "forecast"],
  "properties": {
    "version_hash": { "type": "string" },
    "increments": {
      "type": "array", "minItems": 1,
      "items": {
        "type": "object",
        "required": ["ordinal", "slices", "owner"],
        "properties": {
          "ordinal": { "type": "integer", "minimum": 0 },
          "name":    { "type": "string" },
          "slices":  { "type": "array", "items": { "type": "string", "pattern": "^SLC-[0-9]{4}$" } },
          "owner":   { "type": "string" },
          "is_walking_skeleton": { "type": "boolean" }
        }
      }
    },
    "capacity": {
      "type": "object",
      "required": ["binding_constraint", "review_rate", "integration_rate"],
      "properties": {
        "binding_constraint": { "enum": ["review", "integration", "authoring"] },
        "review_rate":        { "type": "number" },
        "integration_rate":   { "type": "number" },
        "assumptions_used":   { "type": "array", "items": { "type": "string" },
                                "description": "Every default used because the answer was unknown" }
      }
    },
    "forecast": {
      "type": "object",
      "required": ["band", "agreement_rate", "restale_after"],
      "properties": {
        "duration_days":  { "type": "number" },
        "band":           { "enum": ["±20%", "±40%", "±80%"] },
        "agreement_rate": { "type": "number" },
        "restale_after":  { "type": "string", "description": "Always: completion of Increment 0" },
        "recommendation": { "type": ["string","null"] }
      }
    },
    "priority_conflicts": { "type": "array", "items": { "type": "string" },
                            "description": "Where stated business order conflicts with dependency or blast radius. Flagged, never overridden." }
  }
}
```

## coverage.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "coverage.schema.json",
  "title": "Coverage",
  "type": "object",
  "required": ["slice", "denominator", "total", "covered", "passing"],
  "properties": {
    "slice":       { "type": "string" },
    "denominator": { "enum": ["behaviors", "acceptance_criteria"],
                     "description": "SEAM S1.4 — never hard-code. v1 uses 'behaviors'." },
    "total":       { "type": "integer" },
    "covered":     { "type": "integer" },
    "passing":     { "type": "integer" },
    "happy_path":  { "type": "object", "properties": { "total": {"type":"integer"}, "covered": {"type":"integer"} } },
    "failure_path":{ "type": "object", "properties": { "total": {"type":"integer"}, "covered": {"type":"integer"} },
                     "description": "Reported separately. A suite complete on happy paths only is the characteristic silent failure." }
  }
}
```

## tactical-model.schema.json

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "$id": "tactical-model.schema.json",
  "title": "Tactical Model",
  "type": "object",
  "required": ["slice", "aggregates"],
  "properties": {
    "slice": { "type": "string" },
    "aggregates": {
      "type": "array", "minItems": 1,
      "items": {
        "type": "object",
        "required": ["name", "root", "invariants"],
        "properties": {
          "name":        { "type": "string" },
          "root":        { "type": "string" },
          "entities":    { "type": "array", "items": { "type": "string" } },
          "value_objects": { "type": "array", "items": { "type": "string" } },
          "invariants":  { "type": "array", "minItems": 1,
                           "items": { "type": "object",
                                      "required": ["statement", "behaviors"],
                                      "properties": {
                                        "statement": { "type": "string" },
                                        "behaviors": { "type": "array", "items": { "type": "string", "pattern": "^BHV-[0-9]{4}$" } } } },
                           "description": "At least one. Aggregates without invariants are data bags." }
        }
      }
    },
    "domain_events": { "type": "array", "items": { "type": "object",
                        "properties": { "name": {"type":"string"}, "aggregate": {"type":"string"} } },
                       "description": "Named in past tense" },
    "commands":      { "type": "array", "items": { "type": "object",
                        "properties": { "name": {"type":"string"}, "aggregate": {"type":"string"} } },
                       "description": "Named in the imperative" },
    "policies":      { "type": "array", "items": { "type": "string" } }
  }
}
```

## Remaining schemas

Create with the same conventions, deriving required fields from the artifact's use in `07-stages.md`:

`context.schema.json`, `context-map.schema.json`, `variation-policy.schema.json`, `acceptance-criteria.schema.json`, `coupling.schema.json`, `sequences.schema.json`, `redaction-policy.schema.json`, `cutover-plan.schema.json`, `projection.schema.json`, `graph-node.schema.json`, `graph-edge.schema.json`, `intake.schema.json`.

`context-map.schema.json` must express relationship type as an enum of the standard DDD patterns: `customer-supplier`, `conformist`, `anticorruption-layer`, `shared-kernel`, `published-language`, `open-host-service`, `separate-ways`, `partnership`.
