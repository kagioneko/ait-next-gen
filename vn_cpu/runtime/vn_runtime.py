"""VN-CPU v0.4 Runtime Components

Includes CPLValidator for graph integrity and RollbackManager for state recovery.
"""
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Set

# Configure logging
logger = logging.getLogger("vn-cpu.runtime")

@dataclass
class CPLEdge:
    src: str
    edge_type: str
    dst: str

@dataclass
class Checkpoint:
    instruction_count: int
    ctx_snapshot: Dict[str, Any]
    graph_edges: List[CPLEdge]

class CPLValidator:
    """Enforces logical consistency using a lightweight graph."""
    def __init__(self):
        self.edges: List[CPLEdge] = []
        # Define contradictory pairs
        self.contradictions = [("requires", "violates"), ("allows", "denies")]

    def add_edge(self, src: str, edge_type: str, dst: str):
        self.edges.append(CPLEdge(src, edge_type, dst))

    def validate(self) -> bool:
        """Checks for immediate logical contradictions in the graph."""
        for e1 in self.edges:
            for e2 in self.edges:
                if e1.src == e2.src and e1.dst == e2.dst:
                    for c_a, c_b in self.contradictions:
                        if (e1.edge_type == c_a and e2.edge_type == c_b) or \
                           (e1.edge_type == c_b and e2.edge_type == c_a):
                            logger.error(f"⚡ [CPL CONFLICT] {e1.src} both {c_a} and {c_b} {e1.dst}!")
                            return False
        return True

class RollbackManager:
    """Manages system checkpoints and IRQ-triggered recovery."""
    def __init__(self):
        self.history: List[Checkpoint] = []
        
    def save(self, inst_count: int, ctx: Dict[str, Any], edges: List[CPLEdge]):
        # Deep copy the state
        snapshot = Checkpoint(
            instruction_count=inst_count,
            ctx_snapshot=ctx.copy(),
            graph_edges=list(edges)
        )
        self.history.append(snapshot)
        if len(self.history) > 10: self.history.pop(0) # Keep last 10
        logger.info(f"[RB-MGR] Checkpoint saved at instruction {inst_count}")

    def rollback(self) -> Optional[Checkpoint]:
        if len(self.history) < 1:
            logger.critical("!!! CRITICAL: NO CHECKPOINT AVAILABLE FOR ROLLBACK !!!")
            return None
        
        last_safe = self.history.pop()
        logger.warning(f"🔄 [ROLLBACK] Reverting to instruction {last_safe.instruction_count}")
        return last_safe

class VNRuntime:
    """The high-level controller for VN-CPU execution."""
    def __init__(self):
        # Register-like Context Slots (ctx0 - ctxz)
        self.ctx = {str(i): f"Empty register {i}" for i in range(10)}
        self.ctx.update({chr(i): "Uninitialized extension" for i in range(ord('a'), ord('z')+1)})
        
        self.validator = CPLValidator()
        self.rollback_mgr = RollbackManager()
        self.instruction_count = 0
        
        # System Log for observation
        self.history = []

    @property
    def graph(self):
        """TOA Compatibility: Returns an object with an '_edges' attribute."""
        class GraphProxy:
            def __init__(self, edges): self._edges = edges
            def summary(self): return f"nodes={len(self._edges)} edges={len(self._edges)}"
        return GraphProxy(self.validator.edges)

    def _actuate(self, domain, target, action, priority):
        """Interprets the 4-phase instruction into a physical operation."""
        msg = f"Unknown Domain: {domain}"
        
        # Domain: Memory (m)
        if domain == 'm':
            if action == 'r': # Read
                val = self.ctx.get(target, "ERR")
                msg = f"READ register #{target}: {val[:30]}..."
            elif action == 'w': # Write
                # Mock write: updates register with current state info
                self.ctx[target] = f"DATA_WRITTEN_BY_INS_{self.instruction_count}"
                msg = f"WRITE register #{target} with system data."
        
        # Domain: Security (s)
        elif domain == 's':
            val = self.ctx.get(target, "")
            if action == 'a': # Audit
                # Basic leak check
                if "password" in val.lower() or "sk-" in val:
                    msg = f"AUDIT ALERT: Potential leak in #{target}!"
                else:
                    msg = f"AUDIT PASS: #{target} appears clean."
            elif action == 'f': # Fix
                # Basic redaction
                if "password" in val.lower():
                    self.ctx[target] = "[REDACTED]"
                    msg = f"FIX: Neutralized leak in #{target}."
        
        # Domain: Graph (g)
        elif domain == 'g':
            edge_type = "requires" if action == 'r' else "violates"
            self.validator.add_edge("ctx1", edge_type, f"ctx{target}")
            msg = f"GRAPH: Linked ctx1 --({edge_type})--> ctx{target}"

        logger.info(f"[ACTUATOR] {msg}")
        return msg

    def commit(self, instruction: str) -> tuple[bool, str, Optional[str]]:
        """Attempts to commit an instruction. Returns (success, act_msg, irq_report)."""
        if len(instruction) < 4: return False, "Malformed", None
        
        self.instruction_count += 1
        
        # Save checkpoint BEFORE applying potential changes
        self.rollback_mgr.save(self.instruction_count - 1, self.ctx, self.validator.edges)

        # 1. Decode & Actuate
        d, t, a, p = instruction[0], instruction[1], instruction[2], instruction[3]
        act_msg = self._actuate(d, t, a, p)
            
        # 2. Validate
        if not self.validator.validate():
            irq_msg = f"CONFLICT: Domain {d} Target {t} caused graph violation."
            logger.error(f"❌ [IRQ 0x03] {irq_msg} Triggering Rollback.")
            
            safe_state = self.rollback_mgr.rollback()
            if safe_state:
                self.ctx = safe_state.ctx_snapshot
                self.validator.edges = safe_state.graph_edges
                self.instruction_count = safe_state.instruction_count
            return False, act_msg, irq_msg

        logger.info(f"✨ [COMMIT] Instruction {instruction} applied successfully: {act_msg}")
        self.history.append({"inst": instruction, "msg": act_msg})
        return True, act_msg, None
