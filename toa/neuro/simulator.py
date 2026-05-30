"""NeuroState TOA Simulator

Runs emotion snapshots through the TOA machine with CPL conflict analysis.

Flow:
  spirit.db snapshot → TOA #ctx registers → CPL graph → conflict detection
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import List

from ..machine import TOAMachine, TOAMachineState
from ..transpiler import compile_program
from .loader import NeuroSnapshot
from .mapper import CTX_TO_DIM, CPL_PARADOX, build_neuro_dictionary


# ── AIT-Lisp source (compiled once, run per snapshot) ────────────────────────

_NEURO_LISP = """\
; === NeuroState × TOA Emotion Simulator ===
; Note: domain 'e' and actions 'l','t' are pre-registered by build_neuro_dictionary()
; Do NOT include (def ...) here — that would overwrite the native handlers.

; Phase 2: load all 7 emotion dimensions into ctx registers
(do
  (e 1 l 5)
  (e 2 l 5)
  (e 3 l 5)
  (e 4 l 5)
  (e 5 l 5)
  (e 6 l 5)
  (e 7 l 5))

; Phase 3: structural CPL graph (always)
(link 6 creates  4)
(link 4 requires 6)
(link 1 extends  6)
(link 3 cancels  2)
(link 6 cancels  7)

; Phase 4: conditional conflict (paradox) detection
; sorrow > 0.3 → add 'requires calm' (contradicts the 'violates' edge → conflict!)
(link 2 violates 3)
(if (e 2 t 3) (link 2 requires 3))

; guilt > 0.2 → desire paradox
(link 5 violates 1)
(if (e 5 t 2) (link 5 requires 1))

; corruption > 0.1 → openness paradox
(link 7 violates 4)
(if (e 7 t 1) (link 7 requires 4))
"""

_COMPILED_TAPE: str = compile_program(_NEURO_LISP)


# ── result ────────────────────────────────────────────────────────────────────

@dataclass
class SimResult:
    snapshot: NeuroSnapshot
    machine_state: TOAMachineState

    @property
    def conflicts(self):
        return self.machine_state.graph.conflicts()

    @property
    def dominant(self):
        return self.snapshot.dominant(top=3)

    @property
    def is_stable(self) -> bool:
        return len(self.conflicts) == 0

    def summary(self) -> str:
        lines = [f"\n{self.snapshot}"]
        lines.append(self.snapshot.as_ctx_table())

        dom = "  ".join(f"{d}={v:.3f}" for d, v in self.dominant)
        lines.append(f"  → dominant: {dom}")

        if self.conflicts:
            for c in self.conflicts:
                lines.append(f"  ⚡ {c.reason}  ({c.edge_a} × {c.edge_b})")
        else:
            lines.append("  ✓ 安定状態（コンフリクトなし）")

        lines.append(f"  graph: {self.machine_state.graph.summary().strip()}")
        return "\n".join(lines)


# ── runner ────────────────────────────────────────────────────────────────────

def run_simulation(
    snapshots: List[NeuroSnapshot],
    verbose: bool = False,
) -> List[SimResult]:
    """Run each snapshot through the TOA emotion machine."""
    results = []
    for snap in snapshots:
        d = build_neuro_dictionary(snap)
        # mock backend: no LLM calls needed (all handlers are native)
        machine = TOAMachine(dictionary=d, backend=_mock, verbose=verbose)
        state = machine.run(_COMPILED_TAPE)
        results.append(SimResult(snapshot=snap, machine_state=state))
    return results


def _mock(domain, action, ctx_id, priority, ctx_data):
    return None, False, f"[WARN] unhandled backend call: {domain}{action}"
