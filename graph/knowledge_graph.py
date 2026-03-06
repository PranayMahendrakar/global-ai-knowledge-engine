"""
🕸️ Knowledge Graph Module
Builds and manages a structured knowledge graph using NetworkX.
Supports:
- Node/edge CRUD operations
- Graph persistence (JSON/Neo4j)
- Graph analytics
- Visualization export
- Incremental updates
"""

import json
import os
from typing import List, Dict, Optional, Tuple
from datetime import datetime
from pathlib import Path
import networkx as nx
from loguru import logger


class KnowledgeGraph:
    """
    In-memory knowledge graph with persistence support.
    Nodes represent entities; edges represent relationships.
    """

    def __init__(self, storage_path: str = "data/knowledge_graph.json"):
        self.graph = nx.MultiDiGraph()
        self.storage_path = Path(storage_path)
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        self._update_count = 0
        self._last_updated = datetime.now().isoformat()

        # Load existing graph if available
        if self.storage_path.exists():
            self.load()

    def add_entities(self, entities: List[Dict], source: str = ""):
        """Add entities from an extracted article to the graph."""
        added_nodes = 0
        added_edges = 0

        # Add entity nodes
        for entity in entities.get("entities", []) if isinstance(entities, dict) else []:
            node_id = self._normalize_id(entity.get("text", ""))
            if not node_id:
                continue

            if not self.graph.has_node(node_id):
                self.graph.add_node(
                    node_id,
                    label=entity.get("label", "unknown"),
                    text=entity.get("text", ""),
                    sources=[source],
                    first_seen=datetime.now().isoformat(),
                    last_seen=datetime.now().isoformat(),
                    mentions=1,
                    properties=entity.get("properties", {})
                )
                added_nodes += 1
            else:
                # Update existing node
                node_data = self.graph.nodes[node_id]
                node_data["mentions"] = node_data.get("mentions", 0) + 1
                node_data["last_seen"] = datetime.now().isoformat()
                if source and source not in node_data.get("sources", []):
                    node_data.setdefault("sources", []).append(source)

        # Add relation edges
        for relation in entities.get("relations", []) if isinstance(entities, dict) else []:
            subj_id = self._normalize_id(relation.get("subject", ""))
            obj_id = self._normalize_id(relation.get("object", ""))
            predicate = relation.get("predicate", "related_to")

            if subj_id and obj_id:
                # Ensure nodes exist
                if not self.graph.has_node(subj_id):
                    self.graph.add_node(subj_id, label="unknown", text=relation.get("subject", ""), mentions=1)
                if not self.graph.has_node(obj_id):
                    self.graph.add_node(obj_id, label="unknown", text=relation.get("object", ""), mentions=1)

                self.graph.add_edge(
                    subj_id, obj_id,
                    predicate=predicate,
                    confidence=relation.get("confidence", 1.0),
                    source=source,
                    created_at=datetime.now().isoformat()
                )
                added_edges += 1

        self._update_count += 1
        self._last_updated = datetime.now().isoformat()

        if added_nodes > 0 or added_edges > 0:
            logger.debug(f"Graph updated: +{added_nodes} nodes, +{added_edges} edges (total: {self.node_count()}/{self.edge_count()})")

    def add_node(self, node_id: str, **attrs):
        """Add or update a single node."""
        node_id = self._normalize_id(node_id)
        if self.graph.has_node(node_id):
            self.graph.nodes[node_id].update(attrs)
        else:
            self.graph.add_node(node_id, **attrs)

    def add_edge(self, source: str, target: str, predicate: str = "related_to", **attrs):
        """Add a relationship edge between two entities."""
        src_id = self._normalize_id(source)
        tgt_id = self._normalize_id(target)
        self.graph.add_edge(src_id, tgt_id, predicate=predicate, **attrs)

    def query_entity(self, entity_text: str) -> Optional[Dict]:
        """Query information about a specific entity."""
        node_id = self._normalize_id(entity_text)
        if self.graph.has_node(node_id):
            data = dict(self.graph.nodes[node_id])
            data["id"] = node_id
            data["connections"] = self.get_neighbors(node_id)
            return data
        return None

    def get_neighbors(self, node_id: str, depth: int = 1) -> List[Dict]:
        """Get neighboring nodes up to a certain depth."""
        node_id = self._normalize_id(node_id)
        if not self.graph.has_node(node_id):
            return []

        neighbors = []
        for successor in self.graph.successors(node_id):
            edges = self.graph.get_edge_data(node_id, successor)
            for key, edge_data in edges.items():
                neighbors.append({
                    "node_id": successor,
                    "node_data": dict(self.graph.nodes[successor]),
                    "relation": edge_data.get("predicate", "related_to"),
                    "direction": "outgoing"
                })

        for predecessor in self.graph.predecessors(node_id):
            edges = self.graph.get_edge_data(predecessor, node_id)
            for key, edge_data in edges.items():
                neighbors.append({
                    "node_id": predecessor,
                    "node_data": dict(self.graph.nodes[predecessor]),
                    "relation": edge_data.get("predicate", "related_to"),
                    "direction": "incoming"
                })

        return neighbors

    def search_entities(self, query: str, entity_type: Optional[str] = None, limit: int = 20) -> List[Dict]:
        """Search for entities by text similarity."""
        query_lower = query.lower()
        results = []

        for node_id, data in self.graph.nodes(data=True):
            text = data.get("text", node_id).lower()
            if query_lower in text or text in query_lower:
                if entity_type is None or data.get("label") == entity_type:
                    results.append({
                        "id": node_id,
                        "text": data.get("text", node_id),
                        "label": data.get("label", "unknown"),
                        "mentions": data.get("mentions", 1),
                        "last_seen": data.get("last_seen", ""),
                    })

        # Sort by mention count
        results.sort(key=lambda x: x.get("mentions", 1), reverse=True)
        return results[:limit]

    def get_most_connected(self, n: int = 20, entity_type: Optional[str] = None) -> List[Dict]:
        """Get the most connected/mentioned entities."""
        nodes_with_degree = []
        for node_id, data in self.graph.nodes(data=True):
            if entity_type is None or data.get("label") == entity_type:
                degree = self.graph.degree(node_id)
                nodes_with_degree.append({
                    "id": node_id,
                    "text": data.get("text", node_id),
                    "label": data.get("label", "unknown"),
                    "degree": degree,
                    "mentions": data.get("mentions", 1),
                })

        nodes_with_degree.sort(key=lambda x: (x["degree"], x["mentions"]), reverse=True)
        return nodes_with_degree[:n]

    def get_subgraph(self, entity_text: str, hops: int = 2) -> Dict:
        """Extract a subgraph centered on an entity."""
        center_id = self._normalize_id(entity_text)
        if not self.graph.has_node(center_id):
            return {"nodes": [], "edges": []}

        # BFS to get nodes within 'hops' distance
        subgraph_nodes = {center_id}
        current_level = {center_id}

        for _ in range(hops):
            next_level = set()
            for node in current_level:
                next_level.update(self.graph.successors(node))
                next_level.update(self.graph.predecessors(node))
            current_level = next_level - subgraph_nodes
            subgraph_nodes.update(current_level)

        # Build subgraph data
        nodes = []
        for node_id in subgraph_nodes:
            data = dict(self.graph.nodes[node_id])
            nodes.append({"id": node_id, **data})

        edges = []
        for u, v, data in self.graph.edges(data=True):
            if u in subgraph_nodes and v in subgraph_nodes:
                edges.append({"source": u, "target": v, **data})

        return {"nodes": nodes, "edges": edges, "center": center_id}

    def get_stats(self) -> Dict:
        """Get graph statistics."""
        return {
            "node_count": self.node_count(),
            "edge_count": self.edge_count(),
            "update_count": self._update_count,
            "last_updated": self._last_updated,
            "density": nx.density(self.graph),
            "entity_types": self._count_entity_types(),
            "top_entities": self.get_most_connected(10),
        }

    def _count_entity_types(self) -> Dict:
        """Count entities by type."""
        from collections import Counter
        labels = [data.get("label", "unknown") for _, data in self.graph.nodes(data=True)]
        return dict(Counter(labels))

    def node_count(self) -> int:
        return self.graph.number_of_nodes()

    def edge_count(self) -> int:
        return self.graph.number_of_edges()

    def save(self, path: Optional[str] = None):
        """Save graph to JSON file."""
        save_path = Path(path) if path else self.storage_path
        save_path.parent.mkdir(parents=True, exist_ok=True)

        graph_data = {
            "metadata": {
                "node_count": self.node_count(),
                "edge_count": self.edge_count(),
                "saved_at": datetime.now().isoformat(),
                "update_count": self._update_count,
            },
            "nodes": [
                {"id": node_id, **{k: v for k, v in data.items() if isinstance(v, (str, int, float, bool, list))}}
                for node_id, data in self.graph.nodes(data=True)
            ],
            "edges": [
                {"source": u, "target": v, "key": k, **{kk: vv for kk, vv in data.items() if isinstance(vv, (str, int, float, bool))}}
                for u, v, k, data in self.graph.edges(data=True, keys=True)
            ]
        }

        with open(save_path, "w", encoding="utf-8") as f:
            json.dump(graph_data, f, indent=2, ensure_ascii=False)

        logger.info(f"💾 Graph saved: {self.node_count()} nodes, {self.edge_count()} edges → {save_path}")

    def load(self, path: Optional[str] = None):
        """Load graph from JSON file."""
        load_path = Path(path) if path else self.storage_path

        if not load_path.exists():
            logger.warning(f"Graph file not found: {load_path}")
            return

        with open(load_path, "r", encoding="utf-8") as f:
            graph_data = json.load(f)

        self.graph = nx.MultiDiGraph()

        for node in graph_data.get("nodes", []):
            node_id = node.pop("id")
            self.graph.add_node(node_id, **node)

        for edge in graph_data.get("edges", []):
            source = edge.pop("source")
            target = edge.pop("target")
            edge.pop("key", None)
            self.graph.add_edge(source, target, **edge)

        metadata = graph_data.get("metadata", {})
        self._update_count = metadata.get("update_count", 0)
        logger.info(f"📂 Graph loaded: {self.node_count()} nodes, {self.edge_count()} edges from {load_path}")

    def _normalize_id(self, text: str) -> str:
        """Normalize entity text to a consistent node ID."""
        return text.strip().lower().replace(" ", "_").replace("'", "").replace('"', "")[:100]

    def export_for_visualization(self) -> Dict:
        """Export graph in a format suitable for visualization (D3.js/vis.js)."""
        nodes = []
        for node_id, data in self.graph.nodes(data=True):
            nodes.append({
                "id": node_id,
                "label": data.get("text", node_id),
                "group": data.get("label", "unknown"),
                "value": data.get("mentions", 1),
                "title": f"{data.get('text', node_id)} ({data.get('label', 'unknown')})"
            })

        edges = []
        for u, v, data in self.graph.edges(data=True):
            edges.append({
                "from": u,
                "to": v,
                "label": data.get("predicate", ""),
                "arrows": "to"
            })

        return {"nodes": nodes, "edges": edges}
