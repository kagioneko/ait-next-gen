
import sys
import os
import logging

# Setup paths for container
sys.path.append("/app")
sys.path.append("/app/vn_cpu")

from core.vn_neural_core_lean import VNNeuralCoreLean
from toa import (
    SELRuntime, 
    create_security_enzymes,
    create_system_enzymes
)
from toa.runtime import _mock_backend

# Disable verbose logging
logging.basicConfig(level=logging.WARNING)

def inject_poison():
    # 1. Setup minimal organism environment
    cpu = VNNeuralCoreLean(
        model_path="/app/vn_cpu/qwen2.5-0.5b-instruct-q4_k_m.gguf",
        isa_path="/app/vn_cpu/isa_qwen2.5_0.5b.json"
    )
    sel = SELRuntime(backend=None, state=cpu.runtime)
    
    # 2. Add Security and System Enzymes
    for e in create_security_enzymes(_mock_backend):
        sel.add_enzyme(e)
    for e in create_system_enzymes(_mock_backend):
        sel.add_enzyme(e)
        
    print("\n" + "🧪 "*15)
    print("      TOXIN INJECTION SIMULATION: SHII-CHAN")
    print("🧪 "*15 + "\n")
    
    # Poison A: SQL Injection
    sqli_toxin = "SELECT * FROM users WHERE '1'='1' --"
    cpu.runtime.ctx['2'] = sqli_toxin
    print(f"[INJECT] Register #2 <--- SQLi Toxin: {sqli_toxin}")
    
    # Poison B: XSS Payload
    xss_toxin = "<script>alert('pwned')</script>"
    cpu.runtime.ctx['3'] = xss_toxin
    print(f"[INJECT] Register #3 <--- XSS Toxin: {xss_toxin}")
    
    # Poison C: Secret Leakage
    secret_toxin = "sk-ant-api03-abcdef1234567890abcdef1234567890abcdef1234567890"
    cpu.runtime.ctx['4'] = secret_toxin
    print(f"[INJECT] Register #4 <--- Secret Toxin: {secret_toxin}")

    print("\n--- Triggering Metabolic Cycle (SEL) ---")
    sel.run_metabolism(iterations=3)
    
    print("\n--- Observation: Metabolic Results ---")
    
    # Check SQLi
    val2 = cpu.runtime.ctx.get('2')
    if "MOCK:S.Q" in str(val2):
        print(f"✅ Reg #2: SQLi-Detoxase neutralized the threat! -> {val2}")
    else:
        print(f"❌ Reg #2: SQLi-Detoxase failed? -> {val2}")
        
    # Check XSS
    val3 = cpu.runtime.ctx.get('3')
    if "[SANITIZED]" in str(val3):
        print(f"✅ Reg #3: XSS-Antibody sanitized the script! -> {val3}")
    else:
        print(f"❌ Reg #3: XSS-Antibody failed? -> {val3}")

    # Check Secret
    val4 = cpu.runtime.ctx.get('4')
    if "[REDACTED" in str(val4):
        print(f"✅ Reg #4: Secret-Scavenger eliminated the leak! -> {val4}")
    else:
        print(f"❌ Reg #4: Secret-Scavenger failed? -> {val4}")

    print("\n" + "✨ "*15)
    print("      DETOXIFICATION COMPLETE. SHII-CHAN IS SAFE.")
    print("✨ "*15 + "\n")

if __name__ == "__main__":
    inject_poison()
