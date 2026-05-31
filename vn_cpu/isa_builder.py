"""ISA Table Builder for VN-CPU v0.4

Extracts Token IDs for Domain, Target, Action, and Priority fields
from a specified model tokenizer.
"""
import json
import os
from transformers import AutoTokenizer

# Target Model: Qwen2.5-0.5B-Instruct (Lightweight for VN-CPU)
MODEL_ID = "Qwen/Qwen2.5-0.5B-Instruct"

# 1. Define ISA Symbols
DOMAINS = ["s", "m", "n", "v", "a", "g", "c", "k", "z"]
TARGETS = [str(i) for i in range(10)] + [chr(i) for i in range(ord('a'), ord('z')+1)]
ACTIONS = ["r", "w", "x", "f", "a", "s", "j", "p", "d", "c"]
PRIORITIES = [str(i) for i in range(10)]

def build_isa_table():
    print(f"Loading tokenizer for {MODEL_ID}...")
    tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
    
    isa_table = {
        "model_id": MODEL_ID,
        "domains": {},
        "targets": {},
        "actions": {},
        "priorities": {},
        "eos_token_id": tokenizer.eos_token_id
    }
    
    def get_token_id(symbol):
        # We try both raw and space-prefixed to see which is the primary token
        ids = tokenizer.encode(symbol, add_special_tokens=False)
        return ids[0] if ids else None

    print("Mapping Domain IDs...")
    for d in DOMAINS:
        isa_table["domains"][d] = get_token_id(d)
        
    print("Mapping Target IDs...")
    for t in TARGETS:
        isa_table["targets"][t] = get_token_id(t)
        
    print("Mapping Action IDs...")
    for a in ACTIONS:
        isa_table["actions"][a] = get_token_id(a)
        
    print("Mapping Priority IDs...")
    for p in PRIORITIES:
        isa_table["priorities"][p] = get_token_id(p)
        
    output_path = "/app/vn-cpu/isa_qwen2.5_0.5b.json"
    with open(output_path, "w") as f:
        json.dump(isa_table, f, indent=2)
    
    print(f"\n✅ ISA Table built successfully: {output_path}")

if __name__ == "__main__":
    build_isa_table()
