"""CPOSBridge — wires TOA MachineHooks to a CPOS ContextStore

TOA #ctx integers are mapped to CPOS ContextObject IDs using the scheme:
    TOA #04  →  CPOS id "toa:04"

What the bridge does automatically:
  CTX_LOAD   → cpos_store.load("toa:NN")   (auto-creates stub if missing)
  CTX_WRITE  → cpos_obj.data = value       (live sync to CPOS RAM)
  CPL_LINK   → cpos_obj.dependencies updated / invalidate() called
  CONFLICT   → cpos WatchDog invalidation on conflicting ctx nodes
"""
from __future__ import annotations
import sys
from typing import Any, List, Optional

# CPOS imports (hard-fail with helpful message if not found)
try:
    from cpos.registry import ContextObject, ContextRegistry
    from cpos.context_store import ContextStore
except ImportError as e:
    raise ImportError(
        "context-pointer-os not found. "
        "Add its src/ to PYTHONPATH:\n"
        "  export PYTHONPATH=/path/to/context-pointer-os/src:$PYTHONPATH"
    ) from e

from ..graph import CPLEdge, Conflict
from ..machine import MachineHooks


def _toa_id(ctx_id: int) -> str:
    return f"toa:{ctx_id:02d}"


class CPOSBridge(MachineHooks):
    """MachineHooks implementation that keeps CPOS ContextStore in sync with TOA."""

    def __init__(self, cpos_store: Optional[ContextStore] = None, verbose: bool = True):
        if cpos_store is None:
            registry = ContextRegistry()
            cpos_store = ContextStore(registry)
        self.store = cpos_store
        self.verbose = verbose

    # ── helpers ───────────────────────────────────────────────────────────

    def _ensure(self, ctx_id: int) -> ContextObject:
        """Return (or auto-create) the CPOS ContextObject for a TOA ctx register."""
        cid = _toa_id(ctx_id)
        obj = self.store.registry.get(cid)
        if obj is None:
            obj = ContextObject(
                id=cid,
                type="toa.register",
                title=f"TOA Register #{ctx_id:02d}",
                summary=f"Auto-created by TOA for ctx #{ctx_id:02d}",
                source="toa",
                priority=0.5,
                trust_score=1.0,
            )
            self.store.registry.register(obj)
            self._log(f"[CPOS] created register {cid}")
        return obj

    def _log(self, msg: str):
        if self.verbose:
            print(f"  {msg}")

    # ── MachineHooks ─────────────────────────────────────────────────────

    def on_ctx_load(self, ctx_id: int) -> None:
        obj = self._ensure(ctx_id)
        cid = _toa_id(ctx_id)
        if not self.store.active_contexts.get(cid):
            self.store.active_contexts[cid] = obj
            obj.state.loaded = True
        self._log(f"[CPOS] CTX_LOAD → '{cid}' active  (status={obj.status})")

    def on_ctx_write(self, ctx_id: int, value: Any) -> None:
        obj = self._ensure(ctx_id)
        obj.data = value
        obj.state.dirty = True
        self._log(f"[CPOS] write    → '{_toa_id(ctx_id)}'.data = {repr(value)[:50]}")

    def on_exec(self, domain: str, action: str, ctx_id: int, priority: int,
                value: Any, success: bool) -> None:
        obj = self._ensure(ctx_id)
        obj.metadata["last_domain"] = domain
        obj.metadata["last_action"] = action
        obj.metadata["last_priority"] = priority
        obj.metadata["last_success"] = success
        obj.trust_score = max(0.0, min(1.0, obj.trust_score + (0.05 if success else -0.1)))
        self._log(f"[CPOS] exec     → '{_toa_id(ctx_id)}' trust={obj.trust_score:.2f}")

    def on_cpl_link(self, edge: CPLEdge) -> None:
        src_obj = self._ensure(edge.src)
        dst_id  = _toa_id(edge.dst)
        self._ensure(edge.dst)

        match edge.edge_type:
            case "requires":
                if dst_id not in src_obj.dependencies:
                    src_obj.dependencies.append(dst_id)
                    self._log(f"[CPOS] link     → '{_toa_id(edge.src)}' deps += '{dst_id}'")

            case "creates":
                # mark dst as having a parent
                dst_obj = self.store.registry.get(dst_id)
                if dst_obj and dst_obj.parent is None:
                    dst_obj.parent = _toa_id(edge.src)
                    self._log(f"[CPOS] link     → '{dst_id}' parent = '{_toa_id(edge.src)}'")

            case "violates":
                self.store.registry.invalidate(
                    dst_id,
                    reason=f"violated by {_toa_id(edge.src)} via TOA CPL",
                )
                self._log(f"[CPOS] link     → '{dst_id}' invalidated (violated)")

            case "cancels":
                # restore dst if it was invalidated
                dst_obj = self.store.registry.get(dst_id)
                if dst_obj and dst_obj.status == "invalidated":
                    dst_obj.status = "active"
                    dst_obj.invalidated_reason = None
                    self._log(f"[CPOS] link     → '{dst_id}' restored (cancelled)")

            case "extends":
                src_obj.metadata.setdefault("extends", [])
                if dst_id not in src_obj.metadata["extends"]:
                    src_obj.metadata["extends"].append(dst_id)
                    self._log(f"[CPOS] link     → '{_toa_id(edge.src)}' extends '{dst_id}'")

    def on_conflict(self, conflicts: List[Conflict]) -> None:
        for c in conflicts:
            # invalidate the *source* of the violates edge as the aggressor
            violates_edge = (c.edge_a if c.edge_a.edge_type == "violates" else c.edge_b)
            cid = _toa_id(violates_edge.src)
            obj = self.store.registry.get(cid)
            if obj and obj.status != "invalidated":
                self.store.registry.invalidate(
                    cid,
                    reason=f"CPL conflict: {c.reason}",
                )
                self._log(f"[CPOS] conflict → '{cid}' invalidated by watchdog  ({c.reason})")

    # ── introspection ─────────────────────────────────────────────────────

    def dump(self) -> str:
        lines = ["[CPOS ContextStore]"]
        for cid, obj in self.store.registry.registry.items():
            if not cid.startswith("toa:"):
                continue
            active = "ACTIVE" if cid in self.store.active_contexts else "      "
            lines.append(
                f"  {active} {cid}  status={obj.status:<12} "
                f"trust={obj.trust_score:.2f}  "
                f"data={repr(obj.data)[:40]}"
            )
        return "\n".join(lines)
