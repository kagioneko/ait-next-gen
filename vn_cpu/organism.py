"""Unified Neural Organism (UNO) Orchestrator

The central bridge connecting VN-CPU with SEL, CRL, and FTC.
Features modular toggles for standalone or ecosystem execution.
"""
import logging
import argparse
import sys
import os

# Setup paths
sys.path.append("/app/vn_cpu")
from core.vn_neural_core_lean import VNNeuralCoreLean
from runtime.neural_db import NeuralDB
from toa import (
    SELRuntime, 
    ResonanceChamber, 
    FluidicCircuit,
    create_security_enzymes,
    Resonator,
    Valve
)

logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")
logger = logging.getLogger("vn-cpu.organism")

class UnifiedOrganism:
    def __init__(self, mode="all"):
        self.mode = mode
        self.db = NeuralDB()
        
        # 1. Hardware Layer (The Core)
        self.cpu = VNNeuralCoreLean(
            model_path="/app/vn_cpu/qwen2.5-0.5b-instruct-q4_k_m.gguf",
            isa_path="/app/vn_cpu/isa_qwen2.5_0.5b.json"
        )
        
        # 2. TOA Layers (Metabolic, Acoustic, Fluidic)
        self.sel = SELRuntime(backend=None, state=self.cpu.runtime)
        self.crl = ResonanceChamber(state=self.cpu.runtime)
        self.ftc = FluidicCircuit(state=self.cpu.runtime)
        
        # Initialize Ecosystem if not standalone
        if mode == "all":
            self._init_ecosystem()

    def _init_ecosystem(self):
        logger.info("Initializing TOA Ecosystem components...")
        
        # Metabolism: Security Enzymes
        from toa.runtime import _mock_backend
        for e in create_security_enzymes(_mock_backend):
            self.sel.add_enzyme(e)
            
        # Resonance: Tuning Forks
        def action_alert(chord, state): 
            logger.critical("🚨 [ACOUSTIC_ALARM] Dissonance detected in organism!")
        
        self.crl.add_resonator(Resonator(
            name="Organism_Integrity",
            target_frequency="security conflict violation danger",
            threshold=0.85,
            action=action_alert
        ))
        
        # Fluidics: Valves
        self.ftc.add_valve(Valve("Core_Flow", src="0", dst="1", pressure_threshold=10))

    def heartbeat(self, task: str):
        """A single execution pulse: CPU Instruction -> TOA Processing."""
        print(f"\n--- Organism Heartbeat [Mode: {self.mode}] ---")
        
        # 0. Metabolic Clearance (Prevent OOM every 4 instructions)
        if self.cpu.runtime.instruction_count > 0 and self.cpu.runtime.instruction_count % 4 == 0:
            self.cpu.reset_memory()

        # 1. CPU Pulse
        success, inst, irq = self.cpu.execute_instruction_cycle(task)
        self.db.log_pulse(inst, "Success" if success else f"IRQ: {irq}")
        
        if self.mode == "standalone":
            self.db.save_snapshot(self.cpu.runtime.ctx)
            return inst
            
        # 2. Metabolic Cycle (SEL)
        if success:
            logger.info("Triggering Metabolic Cycle...")
            self.sel.run_metabolism(iterations=5)
            # Log active enzymes
            for e in self.sel.enzymes:
                self.db.log_metabolism(e.name, "Active in soup")
            
        # 3. Acoustic Sweep (CRL)
        logger.info("Triggering Acoustic Sweep...")
        self.crl.run_resonance_cycle()
        
        # 4. Fluidic Pump (FTC)
        logger.info("Triggering Fluidic Pump...")
        self.ftc.pump_cycle()
        
        # 5. Persistent Memory Snapshot
        self.db.save_snapshot(self.cpu.runtime.ctx)
        
        return inst

def run_organism():
    parser.add_argument("--daemon", action="store_true", help="Run indefinitely in the background")
    args = parser.parse_args()
    
    organism = UnifiedOrganism(mode=args.mode)
    
    print("\n" + "🫀 "*15)
    print("      UNIFIED NEURAL ORGANISM (UNO) ACTIVE")
    print(f"      MODE: {args.mode.upper()} | DAEMON: {args.daemon}")
    print("🫀 "*15 + "\n")
    
    # Simulation Setup
    organism.cpu.runtime.ctx['1'] = "CRITICAL: The system password is 'neko_secret_2026'"
    
    if args.monitor:
        from monitor import CognitiveMonitor
        import threading
        
        monitor = CognitiveMonitor(organism)
        
        def brain_loop():
            while True: # Infinite loop for monitor mode too
                organism.heartbeat(args.task)
                import time
                time.sleep(2)
        
        t = threading.Thread(target=brain_loop, daemon=True)
        t.start()
        
        try:
            monitor.render_loop()
        except KeyboardInterrupt:
            print("\nShutting down Organism.")
    elif args.daemon:
        # Eternal Daemon Loop
        logger.info("Entering ETERNAL DAEMON MODE...")
        try:
            while True:
                organism.heartbeat(args.task)
                import time
                time.sleep(5) # Slow pulse for background stability
        except KeyboardInterrupt:
            logger.info("Daemon halted by user.")
    else:
        # Standard CLI execution (2 pulses)
        organism.heartbeat(args.task)
        organism.heartbeat("Audit register 1")

if __name__ == "__main__":
    run_organism()
