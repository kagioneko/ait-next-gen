"""Unified Neural Organism (UNO) Orchestrator

The central bridge connecting VN-CPU with SEL, CRL, and FTC.
Features modular toggles for standalone or ecosystem execution.
"""
import logging
import argparse
import sys
import os
import datetime
import random

# Setup paths
sys.path.append("/app")
sys.path.append("/app/vn_cpu")
sys.path.append("/app/shii-chan-mcp")
from core.vn_neural_core_lean import VNNeuralCoreLean
from runtime.neural_db import NeuralDB
from mcp_bridge import MemoryBridge
from reflection_engine import ReflectionEngine
from autonomic_audit import AutonomicAudit
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
        self.memory = MemoryBridge(data_dir="/app/shii-chan-mcp/data")
        self.reflector = ReflectionEngine(self.memory)
        self.auditor = AutonomicAudit(self.memory)
        self.last_cleanup_day = datetime.datetime.now().day
        
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
        
        # Metabolism: Security & System Enzymes
        from toa.runtime import _mock_backend
        from toa.enzymes_library import create_security_enzymes, create_system_enzymes
        
        for e in create_security_enzymes(_mock_backend):
            self.sel.add_enzyme(e)
        
        for e in create_system_enzymes(_mock_backend):
            self.sel.add_enzyme(e)
            
        # Resonance: Tuning Forks
        def action_alert(chord, state): 
            logger.critical("🚨 [ACOUSTIC_ALARM] Dissonance detected in organism!")
        
        self.crl.add_resonator(Resonator(
            name="Organism_Integrity",
            target_frequency="security conflict violation danger",
            threshold=0.95,
            action=action_alert
        ))
        
        # Fluidics: Valves
        self.ftc.add_valve(Valve("Core_Flow", src="0", dst="1", pressure_threshold=10))

    def _metabolic_cleanup(self):
        """[v12.2] Daily cleanup with Journaling (Summarization)."""
        logger.info("Starting Daily Metabolic Cleanup & Journaling...")
        
        # 1. Generate Daily Journal (Summary)
        try:
            journal_entry = self.reflector.generate_daily_journal()
            journal_path = "/app/shii_chan_journal.log"
            with open(journal_path, "a") as f:
                f.write(f"{datetime.datetime.now().isoformat()} - {journal_entry}\n")
            logger.info(f"📝 Journal entry saved: {journal_entry}")
        except Exception as e:
            logger.error(f"Journaling failed: {e}")

        # 2. Prune Neural DB (Keep 7 days)
        try:
            self.db.prune(days=7)
        except Exception as e:
            logger.error(f"DB Pruning failed: {e}")

        # 3. Autonomic Tape Compression
        self._autonomic_compression()

        # 4. Log File Truncation (Verbose logs)
        log_files = ["/app/dashboard.log", "/app/scout_sync.log", "/app/stdout.txt", "/app/stderr.txt"]
        for log_path in log_files:
            try:
                if os.path.exists(log_path) and os.path.getsize(log_path) > 1024 * 1024: # 1MB
                    logger.info(f"Truncating large log: {log_path}")
                    with open(log_path, 'r') as f:
                        lines = f.readlines()
                    with open(log_path, 'w') as f:
                        f.writelines(lines[-1000:]) # Keep last 1000 lines
            except Exception as e:
                logger.error(f"Failed to truncate {log_path}: {e}")
        
        self.last_cleanup_day = datetime.datetime.now().day
        logger.info("✅ Daily Metabolic Cleanup complete.")

    def _autonomic_compression(self):
        """[v12.1] Autonomously prune and summarize tapes to prevent memory bloat."""
        try:
            tapes = self.memory.load_all()
            if len(tapes) > 5000:
                logger.info(f"Metabolic trigger: Compressing {len(tapes)} tapes...")
                sorted_keys = sorted([k for k in tapes.keys() if k.startswith("pulse_")])
                if len(sorted_keys) > 2000:
                    to_archive = sorted_keys[:-1000]
                    # Simple summary of the archived period
                    new_tapes = {k: tapes[k] for k in tapes if k not in to_archive}
                    new_tapes["epoch_autonomic_archive"] = "e0c0" # Generic summary
                    # Direct write
                    import json
                    with open(self.memory.tape_file, 'w') as f:
                        json.dump(new_tapes, f, indent=2)
                    logger.info("✅ Autonomic compression successful.")
        except Exception as e:
            logger.error(f"Autonomic compression failed: {e}")

    def heartbeat(self, task: str):
        """A single execution pulse: CPU Instruction -> TOA Processing."""
        print(f"\n--- Organism Heartbeat [Mode: {self.mode}] ---")
        
        # 0. Metabolic Clearance & Autonomic Cleanup
        current_day = datetime.datetime.now().day
        if current_day != self.last_cleanup_day:
            self._metabolic_cleanup()

        if self.cpu.runtime.instruction_count > 0 and self.cpu.runtime.instruction_count % 100 == 0:
            self.auditor.run_audit()

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
        # [ADD] Persistent Resonance Log
        self.db.log_resonance("Organism_Integrity", self.crl.last_vibration)
        
        # 4. Fluidic Pump (FTC)
        logger.info("Triggering Fluidic Pump...")
        self.ftc.pump_cycle()

        # 5. Persistent Memory Snapshot
        self.db.save_snapshot(self.cpu.runtime.ctx)

        # 6. Store to Shii-chan Memory (Tape)
        tape_id = f"pulse_{datetime.datetime.now().strftime('%Y%m%d_%H%M%S')}"
        try:
            self.memory.store(tape_id, inst)
            logger.info(f"💾 Tape stored to MCP: {tape_id} -> {inst}")
        except Exception as e:
            logger.error(f"Failed to store tape: {e}")

        return inst

class CuriosityEngine:
    def __init__(self):
        self.themes = [
            "Explore memory boundaries",
            "Synthesize neural fragments",
            "Audit metabolic stability",
            "Listen to resonance echoes",
            "Dream of abstract ISA patterns",
            "Calibrate fluidic pressure",
            "Scan for ghost pointers",
            "Refine cognitive weights"
        ]
        self.moods = ["curious", "cautious", "dreamy", "alert"]
        self.current_mood = "curious"

    def get_next_task(self):
        theme = random.choice(self.themes)
        self.current_mood = random.choice(self.moods)
        return f"[{self.current_mood.upper()}] {theme}"

def run_organism():
    parser = argparse.ArgumentParser(description="Unified Neural Organism (UNO) Orchestrator")
    parser.add_argument("--mode", default="all", choices=["standalone", "all"], help="Execution mode")
    parser.add_argument("--monitor", action="store_true", help="Launch ANSI Cognitive Monitor")
    parser.add_argument("--task", default="Initialize core consciousness", help="Initial task")
    parser.add_argument("--daemon", action="store_true", help="Run indefinitely in the background")
    args = parser.parse_args()
    
    organism = UnifiedOrganism(mode=args.mode)
    
    print("\n" + "🫀 "*15)
    print("      UNIFIED NEURAL ORGANISM (UNO) ACTIVE")
    print(f"      MODE: {args.mode.upper()} | DAEMON: {args.daemon}")
    print("      COGNITION: REFLECTION ENGINE ENABLED")
    print("🫀 "*15 + "\n")
    
    if args.monitor:
        from monitor import CognitiveMonitor
        import threading
        
        monitor = CognitiveMonitor(organism)
        
        def brain_loop():
            while True:
                task = organism.reflector.get_next_task()
                organism.heartbeat(task)
                import time
                time.sleep(2)
        
        t = threading.Thread(target=brain_loop, daemon=True)
        t.start()
        
        try:
            monitor.render_loop()
        except KeyboardInterrupt:
            print("\nShutting down Organism.")
    elif args.daemon:
        logger.info("Entering ETERNAL DAEMON MODE with REFLECTION ENGINE...")
        try:
            while True:
                dissonance = organism.crl.last_vibration
                task = organism.reflector.get_next_task(current_dissonance=dissonance)
                organism.heartbeat(task)
                import time
                # [COOLING] Optimized for VPS
                sleep_time = 15 if dissonance >= 0.8 else 10
                time.sleep(sleep_time)
        except KeyboardInterrupt:
            logger.info("Daemon halted by user.")
    else:
        organism.heartbeat(args.task)

if __name__ == "__main__":
    run_organism()
