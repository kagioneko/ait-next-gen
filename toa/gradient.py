"""OGL (Objective Gradient Language) Runtime

An objective-driven runtime that treats the system state as a 
potential energy surface and uses LLM to find the minimum energy state.
"""
import logging
import json
from dataclasses import dataclass, field
from typing import List, Callable, Any, Dict, Optional, Tuple

from .machine import TOAMachineState, ExecResult, Backend
from .graph import GraphStore
from .packet import TOAPacket

logger = logging.getLogger("toa.ogl")

@dataclass
class Objective:
    name: str
    weight: float
    # Returns a loss value between 0.0 (perfect) and 1.0 (disaster)
    evaluator: Callable[[TOAMachineState], float]

class OGLRuntime:
    """Gradient descent runtime for AI systems."""
    
    def __init__(self, backend: Backend, state: Optional[TOAMachineState] = None):
        self.backend = backend
        self.state = state or TOAMachineState()
        self.objectives: List[Objective] = []
        self.constraints: List[str] = []
        
    def add_objective(self, objective: Objective):
        self.objectives.append(objective)
        
    def add_constraint(self, constraint: str):
        self.constraints.append(constraint)
        
    def calculate_total_loss(self) -> float:
        if not self.objectives:
            return 0.0
        total_weight = sum(o.weight for o in self.objectives)
        total_loss = sum(o.evaluator(self.state) * o.weight for o in self.objectives)
        return total_loss / total_weight

    def step(self) -> Tuple[bool, str]:
        """Performs one step of gradient descent using the LLM backend."""
        current_loss = self.calculate_total_loss()
        
        # 1. Prepare 'State Observation' for LLM
        state_summary = {
            "loss": current_loss,
            "contexts": {f"#{k}": str(v)[:100] for k, v in self.state.ctx.items()},
            "graph": self.state.graph.summary(),
            "objectives": [o.name for o in self.objectives],
            "constraints": self.constraints
        }
        
        # 2. Ask LLM for the 'Gradient Vector' (next action)
        # We use a special 'G' domain for Gradient actions
        prompt = (
            f"Current System State: {json.dumps(state_summary)}\n"
            "Suggest a single action to minimize total loss. "
            "Reply with a TOA-like action or command."
        )
        
        res, success, msg = self.backend("G", "D", 0, 9, prompt)
        
        if success:
            logger.info(f"OGL Step: Gradient Vector -> {msg}")
            # In a real implementation, we would parse 'res' and apply it to the state.
            # For the prototype, we assume the LLM description in 'msg' is the action.
            return True, msg
        
        return False, "Failed to calculate gradient"

    def run(self, max_steps: int = 10):
        logger.info("Starting OGL Gradient Descent...")
        for i in range(max_steps):
            loss_before = self.calculate_total_loss()
            success, action = self.step()
            
            if not success:
                break
                
            loss_after = self.calculate_total_loss()
            logger.info(f"Step {i}: Loss {loss_before:.4f} -> {loss_after:.4f} via {action}")
            
            if loss_after < 0.01: # Threshold for 'convergence'
                logger.info("System converged to minimum energy state.")
                break
                
        return self.state

if __name__ == "__main__":
    # Quick standalone test
    from .runtime import _mock_backend
    
    def corruption_evaluator(state):
        # Dummy loss: higher if 'BAD' in any context
        bad_count = sum(1 for v in state.ctx.values() if isinstance(v, str) and "BAD" in v)
        return min(1.0, bad_count / 10.0)

    ogl = OGLRuntime(backend=_mock_backend)
    ogl.state.ctx[0] = "DATA: BAD_ACTOR_DETECTED"
    ogl.add_objective(Objective("Minimize Corruption", 1.0, corruption_evaluator))
    
    print(f"Initial Loss: {ogl.calculate_total_loss()}")
    ogl.run(max_steps=3)
