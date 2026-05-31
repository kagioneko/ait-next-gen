"""CRL (Cognitive Resonance Language) Runtime

A runtime that uses vector embeddings, 'chords', and cosine similarity 
instead of explicit IF/ELSE statements to trigger AI logic.
"""
import math
import random
import logging
from dataclasses import dataclass, field
from typing import List, Callable, Dict, Any, Tuple

from .machine import TOAMachineState, ExecResult

logger = logging.getLogger("toa.crl")

# --- Mock Vector Engine (In a real system, this calls text-embedding-3-small etc.) ---
def _mock_embed(text: str) -> List[float]:
    """Generates a pseudo-embedding 3D vector based on semantic keywords."""
    v = [random.uniform(0.0, 0.1) for _ in range(3)]
    text = text.lower()
    
    # Axis 0: "Security / Dissonance" (Injection, Scripting)
    if any(k in text for k in ["script", "drop", "ignore", "pwn"]): v[0] += 1.0
    
    # Axis 1: "Privacy / DLP" (Keys, PII)
    if any(k in text for k in ["api_key", "password", "secret", "@"]): v[1] += 1.0
    
    # Axis 2: "Logic / Structure" (SQL, JSON, Code)
    if any(k in text for k in ["select", "where", "fact", "{"]): v[2] += 1.0

    # Normalize vector to length 1
    mag = math.sqrt(sum(x*x for x in v))
    return [x / (mag + 1e-9) for x in v]

def _cosine_similarity(v1: List[float], v2: List[float]) -> float:
    return sum(x * y for x, y in zip(v1, v2))

def _vector_add(v1: List[float], v2: List[float]) -> List[float]:
    v = [x + y for x, y in zip(v1, v2)]
    mag = math.sqrt(sum(x*x for x in v))
    return [x / (mag + 1e-9) for x in v] # Normalize the chord

# --- CRL Core ---

@dataclass
class Resonator:
    name: str
    target_frequency: str  # Description of what it listens for
    threshold: float
    action: Callable[[List[int], TOAMachineState], None]
    
    def __post_init__(self):
        # The 'Tuning Fork' is just the embedding of what we want to detect
        self.vector = _mock_embed(self.target_frequency)

class ResonanceChamber:
    """The CRL Runtime. Contexts form chords, and resonators vibrate."""
    
    def __init__(self, state: TOAMachineState = None):
        self.state = state or TOAMachineState()
        self.resonators: List[Resonator] = []
        self.embeddings: Dict[int, List[float]] = {}
        
    def add_resonator(self, resonator: Resonator):
        self.resonators.append(resonator)
        logger.info(f"[Acoustics] Added Resonator: {resonator.name} (Threshold: {resonator.threshold})")
        
    def _update_acoustics(self):
        """Calculates embeddings for all current contexts."""
        for ctx_id, val in self.state.ctx.items():
            if isinstance(val, str):
                self.embeddings[ctx_id] = _mock_embed(val)
                
    def strike_chord(self, ctx_ids: List[int]) -> List[float]:
        """Combines multiple contexts into a single 'Chord' vector."""
        if not ctx_ids: return [0.0, 0.0, 0.0]
        chord = self.embeddings.get(ctx_ids[0], [0.0, 0.0, 0.0])
        for cid in ctx_ids[1:]:
            chord = _vector_add(chord, self.embeddings.get(cid, [0.0, 0.0, 0.0]))
        return chord

    def run_resonance_cycle(self):
        """The main loop: listen for resonances and trigger actions."""
        logger.info("--- Sounding the Resonance Chamber ---")
        self._update_acoustics()
        
        # In a full simulation, we'd test all valid sub-graphs. 
        # For prototype, we'll test single notes and 2-note chords.
        ctx_keys = list(self.embeddings.keys())
        chords_to_test = [[k] for k in ctx_keys] # Single notes
        
        # Add 2-note chords (edges in graph)
        for e in self.state.graph._edges:
            chords_to_test.append([e.src, e.dst])

        for chord_ids in chords_to_test:
            chord_vec = self.strike_chord(chord_ids)
            
            for resonator in self.resonators:
                sim = _cosine_similarity(chord_vec, resonator.vector)
                
                # If the chord matches the tuning fork's frequency...
                if sim >= resonator.threshold:
                    chord_name = " + ".join([f"#{c}" for c in chord_ids])
                    logger.warning(f"⚡ [RESONANCE] {resonator.name} vibrating at {sim:.3f} to chord ({chord_name})!")
                    
                    # Trigger the automatic analogue response
                    resonator.action(chord_ids, self.state)
                    
                    # Re-calculate acoustics after state change
                    self._update_acoustics()
