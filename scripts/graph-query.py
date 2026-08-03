#!/usr/bin/env python3
"""The six named graph queries — scripts/graph-query.py.

Reads .contextrover/graph/{nodes,edges}.jsonl (written by build-graph.py).
No general query language — exactly these six queries and nothing else
(08-knowledge-and-reporting.md §1.2 scope, 12-extension-seams.md §5).

Usage:
  python3 scripts/graph-query.py impact --node <id> [--format text|json] [--dir .contextrover]
  python3 scripts/graph-query.py orphans [--format text|json] [--dir .contextrover]
  python3 scripts/graph-query.py boundary-spans [--format text|json] [--dir .contextrover]
  python3 scripts/graph-query.py coverage [--format text|json] [--dir .contextrover]
  python3 scripts/graph-query.py consumer-blast-radius --interface <id> [--format text|json] [--dir .contextrover]
  python3 scripts/graph-query.py coupling-clusters [--format text|json] [--dir .contextrover]
"""
import argparse
import json
from pathlib import Path


def load_jsonl(path):
    if not path.exists():
        return []
    out = []
    for line in path.read_text().splitlines():
        if line.strip():
            out.append(json.loads(line))
    return out


def load_graph(base):
    nodes = load_jsonl(base / "graph" / "nodes.jsonl")
    edges = load_jsonl(base / "graph" / "edges.jsonl")
    return {n["id"]: n for n in nodes}, edges


def q_impact(nodes, edges, start):
    """Everything reachable from a service or topic (forward traversal along edges)."""
    adj = {}
    for e in edges:
        adj.setdefault(e["from"], []).append(e["to"])
    seen = set()
    frontier = [start]
    while frontier:
        cur = frontier.pop()
        for nxt in adj.get(cur, []):
            if nxt not in seen:
                seen.add(nxt)
                frontier.append(nxt)
    return sorted(seen)


def q_orphans(nodes, edges):
    """Behaviors with no context, contexts with no behaviors."""
    behavior_ids = {n["id"] for n in nodes.values() if n["type"] == "Behavior"}
    context_ids = {n["id"] for n in nodes.values() if n["type"] == "Context"}
    behaviors_with_context = {e["from"] for e in edges if e["type"] == "belongs-to" and e["to"] in context_ids}
    contexts_with_behaviors = {e["to"] for e in edges if e["type"] == "belongs-to" and e["from"] in behavior_ids}
    return {
        "behaviors_without_context": sorted(behavior_ids - behaviors_with_context),
        "contexts_without_behaviors": sorted(context_ids - contexts_with_behaviors),
    }


def q_boundary_spans(nodes, edges):
    """Behaviors touching more than one target service. Warning-level in trace-lint; sagas are legitimate."""
    out = []
    for n in nodes.values():
        if n["type"] != "Behavior":
            continue
        targets = n.get("target_services") or []
        if len(targets) > 1:
            out.append({"id": n["id"], "label": n.get("label"), "target_services": sorted(targets)})
    return sorted(out, key=lambda x: x["id"])


def q_coverage(nodes, edges):
    """Behaviors with no 'covers' edge from a Test."""
    behavior_ids = {n["id"] for n in nodes.values() if n["type"] == "Behavior"}
    covered = {e["to"] for e in edges if e["type"] == "covers"}
    return sorted(behavior_ids - covered)


def q_consumer_blast_radius(nodes, edges, interface_id):
    """Who breaks if this Interface changes."""
    return sorted({e["from"] for e in edges if e["type"] == "consumes" and e["to"] == interface_id})


def q_coupling_clusters(nodes, edges):
    """Components that co-change, as boundary evidence (union-find over co-changes-with edges)."""
    parent = {}

    def find(x):
        parent.setdefault(x, x)
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(a, b):
        ra, rb = find(a), find(b)
        if ra != rb:
            parent[ra] = rb

    for e in edges:
        if e["type"] == "co-changes-with":
            union(e["from"], e["to"])

    clusters = {}
    for node_id in parent:
        clusters.setdefault(find(node_id), set()).add(node_id)

    result = [sorted(members) for members in clusters.values() if len(members) > 1]
    result.sort(key=lambda c: (-len(c), c))
    return result


QUERIES = {
    "impact": "everything reachable from a service or topic",
    "orphans": "behaviors with no context, contexts with no behaviors",
    "boundary-spans": "behaviors touching more than one target service",
    "coverage": "behaviors with no covers edge from a Test",
    "consumer-blast-radius": "who breaks if this interface changes",
    "coupling-clusters": "components that co-change, as boundary evidence",
}


def render_text(query, result):
    lines = [f"# {query} — {QUERIES[query]}"]
    if isinstance(result, dict):
        for k, v in result.items():
            lines.append(f"{k}:")
            lines.extend(f"  {item}" for item in v) if v else lines.append("  (none)")
    elif isinstance(result, list) and result and isinstance(result[0], dict):
        lines.extend(f"  {item}" for item in result)
    elif isinstance(result, list) and result and isinstance(result[0], list):
        for i, cluster in enumerate(result):
            lines.append(f"cluster {i + 1} ({len(cluster)} members): {', '.join(cluster)}")
    else:
        lines.extend(f"  {item}" for item in result) if result else lines.append("  (none)")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("query", choices=sorted(QUERIES))
    parser.add_argument("--node", help="node id, for: impact")
    parser.add_argument("--interface", help="Interface id, for: consumer-blast-radius")
    parser.add_argument("--format", choices=["text", "json"], default="text")
    parser.add_argument("--dir", default=".contextrover")
    args = parser.parse_args()

    nodes, edges = load_graph(Path(args.dir))

    if args.query == "impact":
        if not args.node:
            parser.error("impact requires --node <id>")
        result = q_impact(nodes, edges, args.node)
    elif args.query == "orphans":
        result = q_orphans(nodes, edges)
    elif args.query == "boundary-spans":
        result = q_boundary_spans(nodes, edges)
    elif args.query == "coverage":
        result = q_coverage(nodes, edges)
    elif args.query == "consumer-blast-radius":
        if not args.interface:
            parser.error("consumer-blast-radius requires --interface <id>")
        result = q_consumer_blast_radius(nodes, edges, args.interface)
    else:
        result = q_coupling_clusters(nodes, edges)

    print(json.dumps(result, indent=2) if args.format == "json" else render_text(args.query, result))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
