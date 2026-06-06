import json
import logging
import datetime
from pathlib import Path

logger = logging.getLogger("vn-cpu.audit")

class AutonomicAudit:
    def __init__(self, memory_bridge):
        self.memory = memory_bridge
        self.threshold = 500
        self.target_size = 250

    def calculate_score(self, tid, tval):
        """Advanced L1 Scoring: Evaluate the cognitive value of a tape."""
        score = 0
        
        # 1. Critical Markers
        if any(mark in tid for mark in ["memo_", "challenge_", "idea_", "session_"]):
            return 1000 # Immortal memories
            
        # 2. Domain-based Value
        if tval.startswith("c"): score += 50 # Core logic is vital
        elif tval.startswith("s"): score += 40 # Security is high priority
        elif tval.startswith("v"): score += 30 # Void/New discovery
        elif tval.startswith("n"): score += 20 # Neural updates
        
        # 3. Explicit Priority (4th char of TOA)
        if len(tval) >= 4 and tval[3].isdigit():
            score += int(tval[3]) * 5
            
        # 4. Action Value (3rd char)
        if len(tval) >= 3:
            action = tval[2]
            if action in "mxf": score += 10 # Mutate, X-ray, Fix
            elif action in "r": score += 5  # Read
            
        return score

    def run_audit(self):
        try:
            tapes = self.memory.load_all()
            if len(tapes) < self.threshold:
                return

            logger.info(f"Metabolic trigger: Advanced Autonomic Audit started ({len(tapes)} tapes).")
            
            # Identify pulse tapes
            pulses = []
            non_pulses = {}
            for tid, val in tapes.items():
                if tid.startswith("pulse_"):
                    pulses.append({"id": tid, "val": val, "score": self.calculate_score(tid, val)})
                else:
                    non_pulses[tid] = val

            # Sort pulses by score (desc) then by time (desc)
            pulses.sort(key=lambda x: (x["score"], x["id"]), reverse=True)
            
            # Keep top N
            kept_pulses = pulses[:self.target_size]
            discarded = pulses[self.target_size:]

            # Semantic Clustering (L2 Placeholder): 
            # If we discard a lot of similar domain tapes, create a summary
            domain_counts = {}
            for d in discarded:
                dom = d["val"][0] if d["val"] else "?"
                domain_counts[dom] = domain_counts.get(dom, 0) + 1

            new_tapes = non_pulses
            for p in kept_pulses:
                new_tapes[p["id"]] = p["val"]

            # Add Meta-Tapes for discarded clusters
            ts = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            for dom, count in domain_counts.items():
                if count > 5:
                    summary_id = f"meta_cluster_{ts}_{dom}"
                    # Encoding: [dom]0z[count_hex]
                    count_hex = hex(min(15, count // 10))[2:]
                    new_tapes[summary_id] = f"{dom}0z{count_hex}"

            # Persist
            with open(self.memory.tape_file, 'w') as f:
                json.dump(new_tapes, f, indent=2)
            
            logger.info(f"✅ Advanced Audit complete. Retained {len(new_tapes)} high-signal memories.")
            
        except Exception as e:
            logger.error(f"Advanced Audit failed: {e}")
