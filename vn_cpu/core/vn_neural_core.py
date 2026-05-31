"""VN-CPU v0.4 Neural Core Implementation

Integrates a real LLM (Qwen2.5-0.5B) with the Phase-based Sampler Mask
and the Neural Throttle.
"""
import time
import json
import torch
import logging
from transformers import AutoModelForCausalLM, AutoTokenizer
from typing import List, Dict, Any

# Setup path to import local modules
import sys
sys.path.append("/app/vn-cpu")
from runtime.vn_runtime import VNRuntime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
logger = logging.getLogger("vn-cpu.neural")

class VNNeuralCore:
    def __init__(self, model_id: str, isa_path: str):
        logger.info(f"Loading Neural Core: {model_id}...")
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        # Use CPU only for VPS compatibility, float32/bfloat16 depending on support
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id, 
            torch_dtype=torch.float32,
            device_map="cpu"
        )
        
        with open(isa_path, "r") as f:
            self.isa = json.load(f)
            
        self.runtime = VNRuntime()
        self.phase = 0
        self.throttle_ms = 10 # Neural Throttle: 10ms per token
        
    def get_allowed_tokens(self) -> List[int]:
        if self.phase == 0: return list(self.isa["domains"].values())
        if self.phase == 1: return list(self.isa["targets"].values())
        if self.phase == 2: return list(self.isa["actions"].values())
        if self.phase == 3: return list(self.isa["priorities"].values())
        return []

    def execute_instruction_cycle(self, prompt: str):
        """Generates one 4-token instruction using logit masking."""
        inputs = self.tokenizer(prompt, return_tensors="pt")
        input_ids = inputs["input_ids"]
        
        instruction_tokens = []
        
        for p in range(4):
            self.phase = p
            
            # Forward pass
            with torch.no_grad():
                outputs = self.model(input_ids)
                logits = outputs.logits[:, -1, :]
            
            # Apply VN Sampler Mask
            allowed_ids = self.get_allowed_tokens()
            mask = torch.full_like(logits, float("-inf"))
            mask[:, allowed_ids] = 0
            masked_logits = logits + mask
            
            # Deterministic Sampling (Greedy)
            next_token_id = torch.argmax(masked_logits, dim=-1).unsqueeze(0)
            
            # Decode and Store
            token_str = self.tokenizer.decode(next_token_id[0])
            instruction_tokens.append(token_str.strip())
            
            # Update input_ids for next step
            input_ids = torch.cat([input_ids, next_token_id], dim=-1)
            
            # Neural Throttle
            time.sleep(self.throttle_ms / 1000.0)
            logger.info(f"[VN-CLK] Phase {p}: Token '{instruction_tokens[-1]}' generated.")

        full_inst = "".join(instruction_tokens)
        logger.info(f"✅ [NEURAL-COMMIT] Generated: {full_inst}")
        
        # Pass to Runtime for Validation and State Update
        self.runtime.commit(full_inst)
        return full_inst

def run_neural_simulation():
    print("\n" + "🧠 "*15)
    print("      VN-CPU v0.4 NEURAL CORE ACTIVE")
    print("      (Qwen2.5-0.5B + Sampler Mask)")
    print("🧠 "*15 + "\n")
    
    core = VNNeuralCore(
        model_id="Qwen/Qwen2.5-0.5B-Instruct",
        isa_path="/app/vn-cpu/isa_qwen2.5_0.5b.json"
    )
    
    # Example Prompt: Tell the CPU what to do
    prompt = "Task: Inspect user input and suggest a security action."
    
    print(f"Input Prompt: {prompt}")
    for _ in range(3):
        core.execute_instruction_cycle(prompt)

if __name__ == "__main__":
    run_neural_simulation()
