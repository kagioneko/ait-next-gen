"""SEL (Semantic Enzyme Language) Runtime

A metabolic AI runtime where enzymes (processing units) react with 
substrates (#ctx registers and graph edges) in a soup (context store).
"""
import random
import logging
from dataclasses import dataclass, field
from typing import List, Callable, Any, Dict, Optional, Tuple

from .machine import TOAMachineState, ExecResult, Backend
from .graph import GraphStore, CPLEdge
from .packet import TOAPacket

logger = logging.getLogger("toa.sel")

@dataclass
class Enzyme:
    name: str
    lock: Callable[[int, Any, TOAMachineState], bool]
    action: Callable[[int, Any, TOAMachineState], ExecResult]

class SELRuntime:
    """Metabolic runtime that replaces the sequential IP-based execution."""
    
    def __init__(self, backend: Backend, state: Optional[TOAMachineState] = None):
        self.backend = backend
        self.state = state or TOAMachineState()
        self.enzymes: List[Enzyme] = []
        self.max_reactions = 100
        self.stability_threshold = 3 # Stop if no reactions for N turns
        
    def add_enzyme(self, enzyme: Enzyme):
        self.enzymes.append(enzyme)
        
    def register_standard_enzymes(self):
        """Adds some basic 'metabolic' enzymes."""
        # Example: An enzyme that 'cleans' unverified inputs
        def lock_cleaner(ctx_id, val, state):
            return isinstance(val, str) and "UNTRUSTED" in val
            
        def action_cleaner(ctx_id, val, state):
            res, success, msg = self.backend("S", "C", ctx_id, 9, val)
            if success:
                state.ctx[ctx_id] = res
            return ExecResult(packet=None, value=res, success=success, msg=msg)

        self.add_enzyme(Enzyme("Sanitizer", lock_cleaner, action_cleaner))

    def run_metabolism(self, iterations: int = 100):
        """The main metabolic loop."""
        logger.info("Starting SEL Metabolism...")
        no_reaction_count = 0
        
        for i in range(iterations):
            reaction_occurred = False
            
            # 1. Randomly sample substrates (active contexts)
            active_ids = list(self.state.ctx.keys())
            if not active_ids:
                break
                
            random.shuffle(active_ids)
            
            for ctx_id in active_ids:
                val = self.state.ctx[ctx_id]
                
                # 2. Try to find a fitting enzyme
                fitting_enzymes = [e for e in self.enzymes if e.lock(ctx_id, val, self.state)]
                
                if fitting_enzymes:
                    # 3. Trigger reaction (pick one if multiple match)
                    enzyme = random.choice(fitting_enzymes)
                    logger.info(f"Metabolic Reaction: {enzyme.name} applied to #{ctx_id}")
                    
                    result = enzyme.action(ctx_id, val, self.state)
                    reaction_occurred = True
                    no_reaction_count = 0
                    break # One reaction per 'step' to maintain stability
            
            if not reaction_occurred:
                no_reaction_count += 1
                if no_reaction_count >= self.stability_threshold:
                    logger.info(f"Metabolism reached stability at iteration {i}")
                    break
                    
        return self.state

if __name__ == "__main__":
    # Quick standalone test
    from .runtime import _mock_backend
    
    sel = SELRuntime(backend=_mock_backend)
    sel.state.ctx[0] = "INPUT: UNTRUSTED DATA"
    sel.register_standard_enzymes()
    
    print("Before:", sel.state.ctx)
    sel.run_metabolism(iterations=10)
    print("After:", sel.state.ctx)
