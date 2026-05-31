"""Integrated VN-CPU Simulation

Connects the Sampler Mock with the CPL Validator and Rollback Manager.
"""
import sys
import os
import logging

# Setup path to import local modules
sys.path.append("/app/vn-cpu")

from core.vn_sampler_mock import VNSamplerMock
from runtime.vn_runtime import VNRuntime

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
logger = logging.getLogger("vn-cpu.system")

def run_integrated_simulation():
    print("\n" + "⚙️  "*15)
    print("      VN-CPU v0.4 INTEGRATED RUNTIME")
    print("      (Sampler + Validator + Rollback)")
    print("⚙️  "*15 + "\n")
    
    sampler = VNSamplerMock("/app/vn-cpu/isa_qwen2.5_0.5b.json")
    runtime = VNRuntime()
    
    # We will run until a conflict is detected and rolled back
    for i in range(20):
        instruction = sampler.step()
        
        if instruction:
            # Try to commit
            success = runtime.commit(instruction)
            
            if not success:
                logger.warning("System state preserved via Rollback. Continuing...")
                # After rollback, the sampler will just keep going 
                # (in real life, we might jump to an IRQ handler)

if __name__ == "__main__":
    run_integrated_simulation()
