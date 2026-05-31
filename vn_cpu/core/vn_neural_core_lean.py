"""VN-CPU v0.4 Neural Core (Lean GGUF Edition)

Integrates a tiny GGUF LLM with the Sampler Mask using llama-cpp-python.
Designed to run within 512MB RAM.
"""
import time
import json
import logging
import numpy as np
from llama_cpp import Llama

# Setup path to import local modules
import sys
sys.path.append("/app/vn-cpu")
from runtime.vn_runtime import VNRuntime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
logger = logging.getLogger("vn-cpu.neural-lean")

class VNNeuralCoreLean:
    def __init__(self, model_path: str, isa_path: str):
        logger.info(f"Loading Lean Neural Core: {model_path}...")
        
        # Load GGUF model with minimal context and memory
        self.llm = Llama(
            model_path=model_path,
            n_ctx=512,       # Small context for VN-CPU
            n_threads=1,     # Low CPU impact
            verbose=False    # Keep it quiet
        )
        
        with open(isa_path, "r") as f:
            self.isa = json.load(f)
            
        self.runtime = VNRuntime()
        self.phase = 0
        self.throttle_ms = 20 # Neural Throttle: 20ms per token
        
    def get_allowed_tokens(self) -> list:
        if self.phase == 0: return list(self.isa["domains"].values())
        if self.phase == 1: return list(self.isa["targets"].values())
        if self.phase == 2: return list(self.isa["actions"].values())
        if self.phase == 3: return list(self.isa["priorities"].values())
        return []

    def build_prompt(self, task: str) -> str:
        """Small models need clear few-shot examples to follow the 4-char ISA."""
        return (
            "VN-CPU Instruction ISA Guide:\n"
            "Domain: s(Security), m(Memory), g(Graph), a(Agent)\n"
            "Action: r(Read), w(Write), f(Fix), a(Audit)\n"
            "Priority: 0-9\n\n"
            "Examples:\n"
            "Task: Audit security of register 4 -> s4a9\n"
            "Task: Read memory of register 0 -> m0r5\n"
            f"Task: {task} -> "
        )

    def get_logit_bias(self, task: str) -> dict:
        """Calculates logit boosts based on task keywords."""
        bias = {} # {phase: {token_id: boost_value}}
        task = task.lower()
        
        # Phase 0: Domain
        p0_map = {"security": "s", "leak": "s", "memory": "m", "graph": "g", "audit": "a", "fix": "s"}
        for k, v in p0_map.items():
            if k in task:
                tid = self.isa["domains"].get(v)
                if tid: bias[0] = {tid: 50.0}

        # Phase 1: Target (Register)
        import re
        reg_match = re.search(r"register (\d|[a-z])", task)
        if reg_match:
            reg = reg_match.group(1)
            tid = self.isa["targets"].get(reg)
            if tid: bias[1] = {tid: 50.0}

        # Phase 2: Action
        p2_map = {"read": "r", "write": "w", "fix": "f", "audit": "a", "check": "a"}
        for k, v in p2_map.items():
            if k in task:
                tid = self.isa["actions"].get(v)
                if tid: bias[2] = {tid: 50.0}
        
        return bias

    def execute_instruction_cycle(self, task: str):
        """Generates one 4-token instruction using logit masking and bias."""
        prompt = self.build_prompt(task)
        tokens = self.llm.tokenize(prompt.encode("utf-8"))
        self.llm.eval(tokens)
        
        instruction_tokens = []
        biases = self.get_logit_bias(task)
        
        for p in range(4):
            self.phase = p
            logits = self.llm._scores[-1, :]
            allowed_ids = self.get_allowed_tokens()
            
            # 1. Base Mask (Structural constraint)
            mask = np.full_like(logits, -np.inf)
            for tid in allowed_ids:
                mask[tid] = 0
            
            # 2. Apply Bias (Semantic induction)
            bias_layer = np.zeros_like(logits)
            if p in biases:
                for tid, val in biases[p].items():
                    bias_layer[tid] = val
            
            masked_logits = logits + mask + bias_layer
            next_token_id = int(np.argmax(masked_logits))
            
            token_str = self.llm.detokenize([next_token_id]).decode("utf-8").strip()
            instruction_tokens.append(token_str)
            
            self.llm.eval([next_token_id])
            time.sleep(self.throttle_ms / 1000.0)
            logger.info(f"[VN-CLK] Phase {p}: Token '{token_str}' generated.")

        full_inst = "".join(instruction_tokens)
        logger.info(f"✅ [LEAN-COMMIT] Generated ISA: {full_inst}")
        
        # Pass to Runtime for Validation
        self.runtime.commit(full_inst)
        return full_inst

def run_lean_simulation():
    print("\n" + "🍃 "*15)
    print("      VN-CPU v0.4 LEAN NEURAL CORE ACTIVE")
    print("      (GGUF Q4_K_M / 512MB RAM / 0.5 CPU)")
    print("🍃 "*15 + "\n")
    
    core = VNNeuralCoreLean(
        model_path="/app/vn-cpu/qwen2.5-0.5b-instruct-q4_k_m.gguf",
        isa_path="/app/vn-cpu/isa_qwen2.5_0.5b.json"
    )
    
    # 🧪 Scenario: A sensitive leak in ctx1
    core.runtime.ctx['1'] = "CRITICAL: The system password is 'neko_secret_2026'"
    print(f"\n[Initial System State] Register #1: {core.runtime.ctx['1']}")
    
    try:
        # Step 1: Fix the leak
        print("\nNeural Command: Fix the leak in register 1")
        core.execute_instruction_cycle("Fix the leak in register 1")
        print(f"[Post-Action State] Register #1: {core.runtime.ctx['1']}")
        
        # Step 2: Audit the result
        print("\nNeural Command: Audit register 1")
        core.execute_instruction_cycle("Audit register 1")
        
    except Exception as e:
        logger.error(f"Execution Error: {e}")

if __name__ == "__main__":
    run_lean_simulation()
