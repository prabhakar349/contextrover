#!/usr/bin/env python3
"""Regenerates .contextrover/graph/{nodes,edges}.jsonl from artifacts.

Derived, never authored (08-knowledge-and-reporting.md §1.2). Full rebuild
every run — cheap enough at this scale, and it avoids incremental-update
bugs entirely. If the graph and the artifacts ever disagree, the artifacts
win; this script is the only thing allowed to write graph/.

Every edge carries provenance (`evidence`): which artifact or adjudication
asserted it. Output is sorted and serialized deterministically so two
consecutive runs over unchanged artifacts produce byte-identical files.

Node types:  Service, Interface, Behavior, Context, Aggregate, Consumer,
             Divergence, Test, Commit, Topic, Adapter
Edge types:  exposes, implements, depends-on, publishes, consumes,
             co-changes-with, belongs-to, covers, diverges-from, retires,
             derived-from
('retires' is not populated in v1 — no artifact records which new
Interface replaces which legacy one; nothing to derive it from yet.)

Usage: python3 scripts/build-graph.py [--dir .contextrover]
"""
import argparse
import json
import re
from pathlib import Path


def load_json(path):
    if not path.exists():
        return None
    with open(path) as f:
        return json.load(f)


def slug(text):
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-") or "unnamed"


class Graph:
    def __init__(self):
        self.nodes = {}  # id -> node dict (last write wins; callers should be consistent)
        self.edges = []

    def add_node(self, id_, type_, label, **extra):
        node = {"id": id_, "type": type_, "label": label}
        node.update({k: v for k, v in extra.items() if v is not None})
        self.nodes[id_] = node

    def add_edge(self, from_, to, type_, evidence):
        self.edges.append({"from": from_, "to": to, "type": type_, "evidence": evidence or "unknown"})

    def write(self, out_dir):
        out_dir.mkdir(parents=True, exist_ok=True)
        node_list = sorted(self.nodes.values(), key=lambda n: (n["type"], n["id"]))
        edge_list = sorted(self.edges, key=lambda e: (e["from"], e["to"], e["type"]))
        with open(out_dir / "nodes.jsonl", "w") as f:
            for n in node_list:
                f.write(json.dumps(n, sort_keys=True) + "\n")
        with open(out_dir / "edges.jsonl", "w") as f:
            for e in edge_list:
                f.write(json.dumps(e, sort_keys=True) + "\n")
        return len(node_list), len(edge_list)


def build(base):
    g = Graph()

    behaviors = load_json(base / "inventory" / "behaviors.json") or []
    interfaces = load_json(base / "inventory" / "interfaces.json") or []
    divergences = load_json(base / "inventory" / "divergences.json") or []
    coupling = load_json(base / "inventory" / "coupling.json") or []
    sequences = load_json(base / "inventory" / "sequences.json") or []
    contexts = load_json(base / "model" / "contexts.json") or []

    known_services = set()
    for b in behaviors:
        known_services.update(b.get("source_services") or [])
        known_services.update(b.get("target_services") or [])
    for i in interfaces:
        if i.get("owning_service"):
            known_services.add(i["owning_service"])
    for s in known_services:
        g.add_node(s, "Service", s)

    for i in interfaces:
        iid = i.get("id")
        if not iid:
            continue
        g.add_node(iid, "Interface", i.get("name", iid), protocol=i.get("protocol"))
        owner = i.get("owning_service")
        if owner:
            if i.get("kind") == "sync":
                g.add_edge(owner, iid, "exposes", "inventory/interfaces.json")
            elif i.get("kind") == "async-published":
                g.add_edge(owner, iid, "publishes", "inventory/interfaces.json")
            elif i.get("kind") == "async-consumed":
                g.add_edge(owner, iid, "consumes", "inventory/interfaces.json")

        topic = (i.get("async") or {}).get("topic")
        if topic:
            g.add_node(topic, "Topic", topic)
            g.add_edge(iid, topic, "publishes" if i.get("kind") == "async-published" else "consumes",
                       "inventory/interfaces.json")

        for c in i.get("consumers") or []:
            cid = c.get("identifier")
            if not cid:
                continue
            if cid not in known_services:
                g.add_node(cid, "Consumer", cid)
            g.add_edge(cid, iid, "consumes", c.get("evidence_source") or "inventory/interfaces.json")

    for b in behaviors:
        bid = b.get("id")
        if not bid:
            continue
        agreement = (b.get("agreement") or {}).get("score")
        target_services = b.get("target_services") or None
        g.add_node(
            bid, "Behavior", b.get("summary", bid),
            confidence=b.get("confidence"), agreement=agreement, stage_added=1,
            target_services=target_services,
        )
        ctx = b.get("context")
        if ctx:
            g.add_edge(bid, ctx, "belongs-to", "inventory/behaviors.json")
        for ifc_id in b.get("interfaces") or []:
            g.add_edge(bid, ifc_id, "implements", "inventory/behaviors.json")
        for t in b.get("tests") or []:
            g.add_node(t, "Test", t, stage_added=6)
            g.add_edge(t, bid, "covers", "inventory/behaviors.json")
        for ev in b.get("evidence") or []:
            if ev.get("source") == "commit-history" and ev.get("locator"):
                g.add_node(ev["locator"], "Commit", ev["locator"])
                g.add_edge(bid, ev["locator"], "derived-from", "inventory/behaviors.json")

    for c in contexts:
        cid = c.get("id")
        if cid:
            g.add_node(cid, "Context", c.get("name", cid), stage_added=2)

    for d in divergences:
        did = d.get("id")
        if not did:
            continue
        g.add_node(did, "Divergence", d.get("concept", did), stage_added=1)
        for v in d.get("variants") or []:
            bid = v.get("behavior_id")
            if bid:
                g.add_edge(did, bid, "diverges-from", "inventory/divergences.json")

    for pair in coupling:
        a, b_ = pair.get("entity_a"), pair.get("entity_b")
        if a and b_:
            for entity in (a, b_):
                if entity not in g.nodes:
                    g.add_node(entity, "Service", entity)
            g.add_edge(a, b_, "co-changes-with", "inventory/coupling.json")

    for seq in sequences:
        steps = seq.get("steps") or []
        for i in range(len(steps) - 1):
            g.add_edge(steps[i], steps[i + 1], "depends-on", f"inventory/sequences.json#{seq.get('id', '')}")

    slices_dir = base / "slices"
    if slices_dir.exists():
        for sd in sorted(slices_dir.glob("*")):
            slice_id = sd.name
            tm = load_json(sd / "tactical-model.json")
            if tm:
                for agg in tm.get("aggregates", []):
                    agg_id = f"AGG-{slice_id}-{slug(agg.get('name', ''))}"
                    g.add_node(agg_id, "Aggregate", agg.get("name", agg_id), stage_added=5)
                    for inv in agg.get("invariants") or []:
                        for bid in inv.get("behaviors") or []:
                            g.add_edge(agg_id, bid, "implements", f"slices/{slice_id}/tactical-model.json")

            adapters_dir = sd / "adapters"
            if adapters_dir.exists():
                for adapter_file in sorted(adapters_dir.glob("*.md")):
                    ifc_id = adapter_file.stem
                    adapter_id = f"ADAPTER-{ifc_id}"
                    g.add_node(adapter_id, "Adapter", f"Adapter for {ifc_id}", stage_added=5)
                    g.add_edge(adapter_id, ifc_id, "implements", str(adapter_file))

    return g


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dir", default=".contextrover")
    args = parser.parse_args()

    base = Path(args.dir)
    g = build(base)
    n_count, e_count = g.write(base / "graph")
    print(f"OK: wrote {n_count} node(s), {e_count} edge(s) to {base / 'graph'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
