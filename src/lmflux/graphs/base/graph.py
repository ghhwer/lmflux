from __future__ import annotations

import uuid
from abc import abstractmethod
from typing import List

import networkx as nx

from lmflux.agents.structure import Agent, Session
from lmflux.agents.components import Context
from lmflux.graphs.utils import show_markdown

# --------------------------------------------
#  Core definitions
# --------------------------------------------
class NodeDefinition:
    """A simple task - the building block of a graph."""

    def __init__(self, name: str):
        self.id: str = str(uuid.uuid4())  # string IDs are easier for Mermaid
        self.name = name

    def __repr__(self) -> str:
        return f"<Node {self.name!r} ({self.id[:8]})>"

class Graph:
    """Directed graph that may contain normal ``NodeDefinition`` objects **and** ``NodeGroupDefinition`` objects."""

    # ------------------------------------------------------------------
    #  Construction / mutation API
    # ------------------------------------------------------------------
    def __init__(self, draw_labels_around=False) -> None:
        self.G = nx.DiGraph()  # holds the actual objects
        self.draw_labels_around = draw_labels_around

    def __add_node__(self, obj: NodeDefinition, _metadata={}) -> None:
        """Add a ``NodeDefinition`` or a ``NodeGroupDefinition`` to the graph."""
        self.G.add_node(
            obj.id,
            label=obj.name,
            obj=obj,
            shape="box" if isinstance(obj, NodeGroupDefinition) else "ellipse",
            _metadata=_metadata
        )

    def __find_object_in_graph_by_name__(self, name:str) -> NodeDefinition:
        for node in self.G.nodes:
            if node.label == name:
                return self.G.nodes[node]["obj"]
    
    def __add_edge__(self, src: NodeDefinition, dst: NodeDefinition, _metadata={}) -> None:
        """Create a directed edge ``src → dst``."""
        self.G.add_edge(src.id, dst.id, _metadata=_metadata)

    # ------------------------------------------------------------------
    #  Mermaid rendering – a **single** recursive implementation
    # ------------------------------------------------------------------
    def to_mermaid(self, direction: str = "TB") -> str:
        """
        Return a Mermaid flow-chart string that represents the whole graph,
        including any nested ``TaskGroup`` sub-graphs.
        """
        lines = [f"graph {direction}"]
        lines.extend(self._to_mermaid_lines(indent=0))
        return "\n".join(lines)

    def _to_mermaid_lines(self, indent: int, label_start="start", label_end="end", has_loopback=False, loopback_label="") -> List[str]:
        """
        Private helper that builds *only* the body lines (no ``graph …`` header).

        ``indent`` denotes the level of visual indentation (4 spaces per level).
        """
        ind = "    " * indent
        body: List[str] = []
        # ---- control getes --------------------------------------------
        if self.draw_labels_around:
            nid_start = str(uuid.uuid4())
            body.append(f"{ind}{nid_start}({label_start})")

            nid_end = str(uuid.uuid4())
            body.append(f"{ind}{nid_end}({label_end})")
            body.append(f"style {nid_start} fill:#ffcc00,stroke:#333,stroke-width:2px,color:#000")
            body.append(f"style {nid_end} fill:#ffcc00,stroke:#333,stroke-width:2px,color:#000")
        # ---- nodes ----------------------------------------------------
        for nid, data in self.G.nodes(data=True):
            label = data["label"]
            body.append(f"{ind}{nid}({label})")

        # ---- edges ----------------------------------------------------
        index, max_index = 0, len(list(self.G.nodes))-2
        first_id, last_id = None, None
        for src, dst, data in self.G.edges(data=True):
            label = data.get("_metadata").get("label")
            if label:
                body.append(f"{ind}{src} --{label}--> {dst}")
            else:
                body.append(f"{ind}{src} --> {dst}")
            if index == 0:
                first_id = src
            if index == max_index:
                last_id = dst
            index += 1
        # >> Check if we need to draw labels around
        if self.draw_labels_around:
            body.append(f"{ind}{nid_start} --> {first_id}")
            body.append(f"{ind}{last_id} --> {nid_end}")
        # >> Check if we need to add a loopback
        if has_loopback:
            body.append(f"{ind}{nid_end} --{loopback_label}--> {nid_start}")
        # ---- recurse into sub-graphs ---------------------------------
        for nid, data in self.G.nodes(data=True):
            obj: NodeDefinition = data["obj"]
            if isinstance(obj, NodeGroupDefinition):
                # Render the inner graph (one level deeper)
                body.extend(obj.to_mermaid(indent + 1))
        return body

    # ------------------------------------------------------------------
    #  Visualization helpers (unchanged, but now use the new renderer)
    # ------------------------------------------------------------------
    def show_mermaid(self, direction: str = "TB") -> None:
        show_markdown(f"```mermaid\n{self.to_mermaid(direction)}\n```")
        

# -------------------------------------------
#  NodeGroup – a node that hides a sub-graph
# -------------------------------------------
class NodeGroupDefinition(NodeDefinition):
    """A node that hides a sub-graph (its own ``TaskGraph``)."""

    def __init__(self, name: str):
        super().__init__(name)
        self.graph = Graph()

    # ------------------------------------------------------------------
    #  Convenience API that proxies to the inner graph
    # ------------------------------------------------------------------
    def add_task(self, task: NodeDefinition) -> None:
        self.graph.add_node(task)

    def add_edge(self, src: NodeDefinition, dst: NodeDefinition) -> None:
        self.graph.add_edge(src, dst)

    # ------------------------------------------------------------------
    #  By default the public ``TaskGroup`` just forwards the rendering
    #  request to its inner graph.  Sub-classes can override this method
    #  to add extra visual elements (see ``IterativeTask`` example below).
    # ------------------------------------------------------------------
    def to_mermaid(self, indent=1) -> list[str]:
        """
        Render the inner graph
        """
        body = [f"subgraph {self.id}[\"{self.name}\"]"]
        inner_body = self.graph._to_mermaid_lines(indent=indent+1)
        body.extend(inner_body)
        body.append("end")
        return body

    def show_mermaid(self, direction: str = "TB") -> None:
        self.graph.show_mermaid(direction)

    def defines_sub_graph(self) -> bool:
        return True