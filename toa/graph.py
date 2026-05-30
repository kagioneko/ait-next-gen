"""CPL (Context-Pointer Language) Graph Layer

Adds directed typed edges between #ctx registers.
Edge types:
  creates   — src produced dst
  requires  — src depends on dst being valid
  violates  — src conflicts with dst
  extends   — src inherits from dst
  cancels   — src invalidates dst
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Tuple


EDGE_TYPES = {"creates", "requires", "violates", "extends", "cancels"}

# pairs that are contradictory when both exist between the same (src, dst)
_CONTRADICTIONS: List[Tuple[str, str]] = [
    ("requires", "violates"),
    ("creates",  "cancels"),
]


@dataclass
class CPLEdge:
    src: int
    edge_type: str
    dst: int

    def __repr__(self):
        return f"#{self.src:02d} =={self.edge_type}==> #{self.dst:02d}"


@dataclass
class Conflict:
    edge_a: CPLEdge
    edge_b: CPLEdge
    reason: str

    def __repr__(self):
        return f"[CONFLICT] {self.edge_a}  ×  {self.edge_b}  ({self.reason})"


class GraphStore:
    """The CPL graph: #ctx nodes + typed edges."""

    def __init__(self):
        self._edges: List[CPLEdge] = []

    # ── mutations ─────────────────────────────────────────────────────────

    def link(self, src: int, edge_type: str, dst: int) -> CPLEdge:
        if edge_type not in EDGE_TYPES:
            raise ValueError(f"Unknown edge type '{edge_type}'. "
                             f"Valid: {sorted(EDGE_TYPES)}")
        edge = CPLEdge(src, edge_type, dst)
        self._edges.append(edge)
        return edge

    def unlink(self, src: int, edge_type: str, dst: int) -> bool:
        before = len(self._edges)
        self._edges = [
            e for e in self._edges
            if not (e.src == src and e.edge_type == edge_type and e.dst == dst)
        ]
        return len(self._edges) < before

    # ── queries ───────────────────────────────────────────────────────────

    def edges_from(self, src: int) -> List[CPLEdge]:
        return [e for e in self._edges if e.src == src]

    def edges_to(self, dst: int) -> List[CPLEdge]:
        return [e for e in self._edges if e.dst == dst]

    def edges_of_type(self, edge_type: str) -> List[CPLEdge]:
        return [e for e in self._edges if e.edge_type == edge_type]

    def reachable(self, src: int, edge_types: Optional[Set[str]] = None) -> Set[int]:
        """BFS: all #ctx reachable from src (optionally filtered by edge type)."""
        visited, queue = set(), [src]
        while queue:
            node = queue.pop()
            if node in visited:
                continue
            visited.add(node)
            for e in self.edges_from(node):
                if edge_types is None or e.edge_type in edge_types:
                    queue.append(e.dst)
        visited.discard(src)
        return visited

    # ── conflict detection ────────────────────────────────────────────────

    def conflicts(self) -> List[Conflict]:
        found: List[Conflict] = []
        edge_index: Dict[Tuple[int, str, int], CPLEdge] = {
            (e.src, e.edge_type, e.dst): e for e in self._edges
        }
        for a_type, b_type in _CONTRADICTIONS:
            for e in self._edges:
                if e.edge_type == a_type:
                    key = (e.src, b_type, e.dst)
                    if key in edge_index:
                        found.append(Conflict(
                            edge_a=e,
                            edge_b=edge_index[key],
                            reason=f"{a_type} ⟂ {b_type}",
                        ))
        return found

    def has_cycle(self) -> bool:
        """Detect directed cycles (all edge types combined)."""
        nodes = {e.src for e in self._edges} | {e.dst for e in self._edges}
        visited, rec_stack = set(), set()

        def dfs(n):
            visited.add(n)
            rec_stack.add(n)
            for e in self.edges_from(n):
                if e.dst not in visited:
                    if dfs(e.dst):
                        return True
                elif e.dst in rec_stack:
                    return True
            rec_stack.discard(n)
            return False

        return any(dfs(n) for n in nodes if n not in visited)

    # ── rendering ─────────────────────────────────────────────────────────

    def render(self, highlight_conflicts: bool = True) -> str:
        if not self._edges:
            return "  (no edges)"
        lines = []
        conflicts = {(c.edge_a.src, c.edge_a.edge_type, c.edge_a.dst)
                     for c in self.conflicts()} if highlight_conflicts else set()
        for e in self._edges:
            tag = " ⚡CONFLICT" if (e.src, e.edge_type, e.dst) in conflicts else ""
            lines.append(f"  {e}{tag}")
        return "\n".join(lines)

    def summary(self) -> str:
        nodes = {e.src for e in self._edges} | {e.dst for e in self._edges}
        c = self.conflicts()
        cyc = self.has_cycle()
        parts = [f"nodes={len(nodes)} edges={len(self._edges)}"]
        if c:
            parts.append(f"conflicts={len(c)} ⚡")
        if cyc:
            parts.append("cycle=detected ⚡")
        return "  " + "  ".join(parts)
