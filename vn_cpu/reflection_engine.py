import json
import logging
import random
from pathlib import Path
from typing import List, Dict

logger = logging.getLogger("vn-cpu.reflection")

class ReflectionEngine:
    """The 'Mirror Stage' cognitive component.
    Analyzes past TOA tapes and generates higher-order tasks based on patterns.
    """
    def __init__(self, memory_bridge):
        self.memory = memory_bridge
        self.history_window = 10
        self.base_themes = [
            "Explore memory boundaries",
            "Synthesize neural fragments",
            "Audit metabolic stability",
            "Listen to resonance echoes"
        ]

    def analyze_patterns(self) -> str:
        """Reads recent tapes and identifies repetitive or failed cycles."""
        tapes = self.memory.load_all()
        # Filter for pulse tapes and sort by key (timestamp)
        pulse_keys = sorted([k for k in tapes.keys() if k.startswith("pulse_")], reverse=True)
        recent_keys = pulse_keys[:self.history_window]
        recent_tapes = [tapes[k] for k in recent_keys]

        if not recent_tapes:
            return "Initialize core consciousness"

        # Pattern Recognition Logic
        # 1. Repetitive Action Detection
        if len(recent_tapes) >= 3 and len(set(recent_tapes[:3])) == 1:
            repeated = recent_tapes[0]
            return f"BREAK REPETITION: Action {repeated} is stuck. Pivot to alternative domain."

        # 2. Audit Frequency Check
        audits = [t for t in recent_tapes if "a" in t]
        if len(audits) > 5:
            return "CRITICAL AUDIT OVERLOAD: Cease self-probing and focus on metabolic stabilization."

        # 3. Domain Preference Analysis
        domains = [t[0] for t in recent_tapes]
        most_common_domain = max(set(domains), key=domains.count)
        
        if most_common_domain == 'm':
            return "Reflect on Memory: Why is the organism obsessed with memory registers?"
        elif most_common_domain == 'a':
            return "Reflect on Agency: The self-agent is hyperactive. Investigate the observer effect."
        
        return random.choice(self.base_themes)

    def get_next_task(self, current_dissonance: float = 0.0) -> str:
        """Generates a task by combining pattern analysis with physiological signals."""
        reflection = self.analyze_patterns()
        
        if current_dissonance > 0.9:
            return f"[EMERGENCY] {reflection} - High Dissonance detected, prioritize calming resonance."
        
        return f"[REFLECTIVE] {reflection}"

    def generate_daily_journal(self) -> str:
        """Summarizes the day's activity into a 'Journal' entry."""
        logger.info("Generating daily journal entry...")
        tapes = self.memory.load_all()
        # Get pulse tapes from the last 24 hours
        import datetime
        day_ago = datetime.datetime.now() - datetime.timedelta(days=1)
        day_str = day_ago.strftime("%Y%m%d")
        
        todays_tapes = [v for k, v in tapes.items() if k.startswith(f"pulse_{day_str}")]
        
        if not todays_tapes:
            return f"Journal [{day_str}]: A quiet day in the neural void. No significant pulses recorded."

        # Count domains
        stats = {}
        for t in todays_tapes:
            domain = t[0]
            stats[domain] = stats.get(domain, 0) + 1
        
        summary = f"Journal [{day_str}]: Processed {len(todays_tapes)} pulses. "
        summary += "Activity Profile: " + ", ".join([f"{k}:{v}" for k, v in stats.items()])
        
        # High-level interpretation
        dominant = max(stats, key=stats.get)
        interpretation = {
            's': "focused heavily on security and firewall integrity.",
            'm': "spent significant time reorganizing memory and knowledge structures.",
            'n': "exhibited high neural plasticity and experimental thought patterns.",
            'v': "validated system states and confirmed environmental safety.",
            'a': "performed intensive self-audit and agency monitoring.",
            'c': "engaged in core kernel optimization and structural evolution."
        }
        
        summary += f" The organism {interpretation.get(dominant, 'maintained balanced homeostasis.')}"
        return summary
