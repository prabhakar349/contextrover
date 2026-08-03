#!/usr/bin/env python3
"""Validate .contextrover/ artifacts against schemas/.

Stdlib only (Constitution C5, REQ-73). Implements a JSON Schema
(draft 2020-12) subset directly: type, required, properties,
additionalProperties, patternProperties, items, enum, const, pattern,
minLength/maxLength, minimum/maximum, minItems/maxItems, format
(date/date-time), $ref (local and cross-file), if/then, not.

Usage: python3 scripts/validate-artifacts.py [--stage N] [--dir .contextrover]
Exit 0 if every artifact found is schema-valid, 1 otherwise.
Errors are printed to stderr as "<file>:<pointer>: <message>".
"""
import argparse
import json
import re
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
SCHEMAS_DIR = SCRIPT_DIR.parent / "schemas"

# (glob relative to --dir, schema $id, container kind)
# container kind: "object" = whole file is one record
#                 "array"  = file is a JSON array, validate each item
#                 "jsonl"  = file is JSON Lines, validate each line
MAPPING = [
    ("state.json", "state.schema.json", "object"),
    ("intake.json", "intake.schema.json", "object"),
    ("gates.jsonl", "gate-entry.schema.json", "jsonl"),
    ("approvals.json", "approval.schema.json", "array"),
    ("workstreams.json", "workstream.schema.json", "array"),
    ("roadmap.json", "roadmap.schema.json", "object"),
    ("retirement.json", "retirement.schema.json", "array"),
    ("migration-waypoints.json", "waypoint.schema.json", "array"),
    ("inventory/behaviors.json", "behavior.schema.json", "array"),
    ("inventory/interfaces.json", "interface.schema.json", "array"),
    ("inventory/divergences.json", "divergence.schema.json", "array"),
    ("inventory/coupling.json", "coupling.schema.json", "array"),
    ("inventory/sequences.json", "sequences.schema.json", "array"),
    ("inventory/redaction-policy.json", "redaction-policy.schema.json", "array"),
    ("consensus/*.json", "adjudication.schema.json", "object"),
    ("adjudications/*.json", "adjudication.schema.json", "object"),
    ("model/contexts.json", "context.schema.json", "array"),
    ("model/context-map.json", "context-map.schema.json", "array"),
    ("model/variation-policy.json", "variation-policy.schema.json", "array"),
    ("slices/*/slice.json", "slice.schema.json", "object"),
    ("slices/*/acceptance-criteria.json", "acceptance-criteria.schema.json", "array"),
    ("slices/*/size.json", "size.schema.json", "object"),
    ("slices/*/tactical-model.json", "tactical-model.schema.json", "object"),
    ("slices/*/verification/coverage.json", "coverage.schema.json", "object"),
    ("contexts/*/cutover-plan.json", "cutover-plan.schema.json", "object"),
    ("graph/nodes.jsonl", "graph-node.schema.json", "jsonl"),
    ("graph/edges.jsonl", "graph-edge.schema.json", "jsonl"),
    ("projections/*.json", "projection.schema.json", "array"),
]

# Patterns validated regardless of --stage: cross-cutting, regenerated at every gate.
ALWAYS = {"state.json", "gates.jsonl", "approvals.json", "graph/nodes.jsonl", "graph/edges.jsonl",
          "projections/*.json", "migration-waypoints.json"}

# Patterns that are the new output of a given stage (07-stages.md §3 "Outputs").
STAGE_PATTERNS = {
    0: {"intake.json"},
    1: {
        "inventory/behaviors.json", "inventory/interfaces.json", "inventory/divergences.json",
        "inventory/coupling.json", "inventory/sequences.json", "inventory/redaction-policy.json",
        "retirement.json", "consensus/*.json",
    },
    2: {
        "model/contexts.json", "model/context-map.json", "model/variation-policy.json",
        "adjudications/*.json", "inventory/divergences.json",
    },
    3: {"workstreams.json", "slices/*/slice.json", "slices/*/acceptance-criteria.json", "slices/*/size.json"},
    4: {"roadmap.json"},
    5: {"slices/*/tactical-model.json"},
    6: {"slices/*/verification/coverage.json"},
    7: set(),
    8: {"contexts/*/cutover-plan.json"},
}


def load_schemas():
    schemas = {}
    for f in sorted(SCHEMAS_DIR.glob("*.schema.json")):
        with open(f) as fh:
            schemas[f.name] = json.load(fh)
    # index by declared $id too, in case it ever differs from filename
    for schema in list(schemas.values()):
        schemas.setdefault(schema["$id"], schema)
    return schemas


def resolve_ref(ref, schemas, current_schema):
    if ref.startswith("#/"):
        target, path = current_schema, ref[2:].split("/")
    elif "#/" in ref:
        file_id, frag = ref.split("#/", 1)
        target, path = schemas[file_id], frag.split("/")
    else:
        return schemas[ref]
    node = target
    for part in path:
        node = node[part]
    return node


def check_type(value, expected):
    types = expected if isinstance(expected, list) else [expected]
    for t in types:
        if t == "object" and isinstance(value, dict):
            return True
        if t == "array" and isinstance(value, list):
            return True
        if t == "string" and isinstance(value, str):
            return True
        if t == "integer" and isinstance(value, int) and not isinstance(value, bool):
            return True
        if t == "number" and isinstance(value, (int, float)) and not isinstance(value, bool):
            return True
        if t == "boolean" and isinstance(value, bool):
            return True
        if t == "null" and value is None:
            return True
    return False


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
DATETIME_RE = re.compile(r"^\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}")


def validate(value, schema, schemas, root_schema, pointer, errors):
    if "$ref" in schema:
        target = resolve_ref(schema["$ref"], schemas, root_schema)
        validate(value, target, schemas, target, pointer, errors)
        return

    if "enum" in schema and value not in schema["enum"]:
        errors.append((pointer, f"value {value!r} not in enum {schema['enum']}"))
        return

    if "const" in schema and value != schema["const"]:
        errors.append((pointer, f"value {value!r} != const {schema['const']!r}"))
        return

    if "type" in schema and not check_type(value, schema["type"]):
        errors.append((pointer, f"expected type {schema['type']}, got {type(value).__name__}"))
        return

    if "not" in schema:
        sub_errors = []
        validate(value, schema["not"], schemas, root_schema, pointer, sub_errors)
        if not sub_errors:
            errors.append((pointer, f"value must not match schema {schema['not']}"))

    if isinstance(value, str):
        if "pattern" in schema and not re.search(schema["pattern"], value):
            errors.append((pointer, f"{value!r} does not match pattern {schema['pattern']!r}"))
        if "minLength" in schema and len(value) < schema["minLength"]:
            errors.append((pointer, f"length {len(value)} < minLength {schema['minLength']}"))
        if "maxLength" in schema and len(value) > schema["maxLength"]:
            errors.append((pointer, f"length {len(value)} > maxLength {schema['maxLength']}"))
        fmt = schema.get("format")
        if fmt == "date" and not DATE_RE.match(value):
            errors.append((pointer, f"{value!r} is not a valid date"))
        if fmt == "date-time" and not DATETIME_RE.match(value):
            errors.append((pointer, f"{value!r} is not a valid date-time"))

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if "minimum" in schema and value < schema["minimum"]:
            errors.append((pointer, f"{value} < minimum {schema['minimum']}"))
        if "maximum" in schema and value > schema["maximum"]:
            errors.append((pointer, f"{value} > maximum {schema['maximum']}"))

    if isinstance(value, list):
        if "minItems" in schema and len(value) < schema["minItems"]:
            errors.append((pointer, f"{len(value)} items < minItems {schema['minItems']}"))
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            errors.append((pointer, f"{len(value)} items > maxItems {schema['maxItems']}"))
        if "items" in schema:
            for i, item in enumerate(value):
                validate(item, schema["items"], schemas, root_schema, f"{pointer}/{i}", errors)

    if isinstance(value, dict):
        for req in schema.get("required", []):
            if req not in value:
                errors.append((pointer, f"missing required field {req!r}"))
        props = schema.get("properties", {})
        pattern_props = schema.get("patternProperties", {})
        additional = schema.get("additionalProperties")
        for key, val in value.items():
            if key in props:
                validate(val, props[key], schemas, root_schema, f"{pointer}/{key}", errors)
                continue
            matched = False
            for pat, subschema in pattern_props.items():
                if re.match(pat, key):
                    matched = True
                    validate(val, subschema, schemas, root_schema, f"{pointer}/{key}", errors)
            if not matched and isinstance(additional, dict):
                validate(val, additional, schemas, root_schema, f"{pointer}/{key}", errors)

    if "if" in schema:
        sub_errors = []
        validate(value, schema["if"], schemas, root_schema, pointer, sub_errors)
        branch = schema.get("then") if not sub_errors else schema.get("else")
        if branch:
            validate(value, branch, schemas, root_schema, pointer, errors)


def validate_document(value, schema, schemas, file_label, errors_out):
    errors = []
    validate(value, schema, schemas, schema, "", errors)
    for pointer, message in errors:
        errors_out.append(f"{file_label}:{pointer or '/'}: {message}")


def validate_file(path, schema_id, kind, schemas, errors_out):
    schema = schemas[schema_id]
    try:
        text = path.read_text()
    except OSError as e:
        errors_out.append(f"{path}:/: could not read file: {e}")
        return

    if kind == "jsonl":
        for i, line in enumerate(text.splitlines()):
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                errors_out.append(f"{path}:line {i + 1}: invalid JSON: {e}")
                continue
            validate_document(obj, schema, schemas, f"{path}:line {i + 1}", errors_out)
        return

    try:
        obj = json.loads(text)
    except json.JSONDecodeError as e:
        errors_out.append(f"{path}:/: invalid JSON: {e}")
        return

    if kind == "array":
        if not isinstance(obj, list):
            errors_out.append(f"{path}:/: expected a JSON array")
            return
        for i, item in enumerate(obj):
            validate_document(item, schema, schemas, f"{path}", errors_out)
    else:
        validate_document(obj, schema, schemas, f"{path}", errors_out)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--stage", type=int, choices=range(0, 9), default=None)
    parser.add_argument("--dir", default=".contextrover")
    args = parser.parse_args()

    schemas = load_schemas()
    base = Path(args.dir)

    if args.stage is None:
        patterns = {p for p, _, _ in MAPPING}
    else:
        patterns = set(ALWAYS) | STAGE_PATTERNS.get(args.stage, set())

    errors = []
    checked = 0
    for glob_pattern, schema_id, kind in MAPPING:
        if glob_pattern not in patterns:
            continue
        for path in sorted(base.glob(glob_pattern)):
            if path.is_file():
                checked += 1
                validate_file(path, schema_id, kind, schemas, errors)

    if errors:
        for line in errors:
            print(line, file=sys.stderr)
        print(f"FAIL: {len(errors)} error(s) across {checked} file(s) checked", file=sys.stderr)
        return 1

    print(f"OK: {checked} file(s) valid")
    return 0


if __name__ == "__main__":
    sys.exit(main())
