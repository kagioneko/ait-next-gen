"""VN-CPU v0.4 Sampler Mock

Simulates the logit-masking and phase-based instruction generation 
using the previously extracted ISA Token ID mapping.
"""
import json
import random
import logging
from typing import List, Dict, Any

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
logger = logging.getLogger("vn-cpu.core")

class VNSamplerMock:
    def __init__(self, isa_path: str):
        with open(isa_path, "r") as f:
            self.isa = json.load(f)
        
        self.phase = 0 # 0: Domain, 1: Target, 2: Action, 3: Priority
        self.instruction_buffer = []
        self.running = True

    def get_allowed_tokens(self) -> List[int]:
        """Returns the set of valid Token IDs for the current phase."""
        if self.phase == 0:
            return list(self.isa["domains"].values())
        elif self.phase == 1:
            return list(self.isa["targets"].values())
        elif self.phase == 2:
            return list(self.isa["actions"].values())
        elif self.phase == 3:
            return list(self.isa["priorities"].values())
        return []

    def sample_token(self) -> int:
        """Simulates constrained sampling (masking everything else to -INF)."""
        allowed = self.get_allowed_tokens()
        
        # In a real VN-CPU, the LLM would output logits here.
        # We simulate this by picking a random ALLOWED token.
        selected_token = random.choice(allowed)
        return selected_token

    def decode_token(self, token_id: int) -> str:
        """Finds the symbol corresponding to a Token ID in the current phase."""
        mapping = {}
        if self.phase == 0: mapping = self.isa["domains"]
        elif self.phase == 1: mapping = self.isa["targets"]
        elif self.phase == 2: mapping = self.isa["actions"]
        elif self.phase == 3: mapping = self.isa["priorities"]
        
        for symbol, tid in mapping.items():
            if tid == token_id:
                return symbol
        return "?"

    def step(self):
        """Executes one clock cycle (1 token generation)."""
        token_id = self.sample_token()
        symbol = self.decode_token(token_id)
        
        self.instruction_buffer.append(symbol)
        logger.info(f"[VN-CLK] Phase {self.phase}: Generated '{symbol}' (ID: {token_id})")
        
        # Advance phase
        self.phase += 1
        if self.phase > 3:
            full_inst = "".join(self.instruction_buffer)
            logger.info(f"✅ [COMMIT] Instruction Complete: {full_inst}")
            
            # Reset for next instruction
            self.instruction_buffer = []
            self.phase = 0
            return full_inst
        return None

def run_simulation(steps: int = 12):
    print("\n" + "⚡ "*15)
    print("      VN-CPU v0.4 NEURAL CORE SIMULATION")
    print("      (Isolated in Docker / 1.0 CPU / 1G RAM)")
    print("⚡ "*15 + "\n")
    
    sampler = VNSamplerMock("/app/vn-cpu/isa_qwen2.5_0.5b.json")
    
    for i in range(steps):
        sampler.step()

if __name__ == "__main__":
    run_simulation()
