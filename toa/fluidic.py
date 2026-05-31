"""FTC (Fluidic Token Circuit) Runtime

Treats context data as a fluid where 'Pressure' is derived from 
string length or token density. Logic is implemented via Valves and Pipes.
"""
import logging
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional

from .machine import TOAMachineState

logger = logging.getLogger("toa.fluidic")

@dataclass
class Valve:
    name: str
    src: str # Source context ID
    dst: str # Destination context ID
    pressure_threshold: int # Minimum string length to open valve
    resistance: float = 1.0 # Multiplier for flow reduction

class FluidicCircuit:
    """Manages the flow of 'Token Fluid' between context slots."""
    
    def __init__(self, state: TOAMachineState = None):
        self.state = state or TOAMachineState()
        self.valves: List[Valve] = []
        
    def add_valve(self, valve: Valve):
        self.valves.append(valve)
        logger.info(f"[Fluidics] Installed Valve: {valve.name} ({valve.src} -> {valve.dst})")

    def pump_cycle(self):
        """Simulates one cycle of fluid flow through the circuit."""
        logger.info("--- Pumping Fluidic Circuit ---")
        changes_occurred = False
        
        # In a real analog system, this happens concurrently.
        # Here we iterate through valves.
        for valve in self.valves:
            src_val = str(self.state.ctx.get(valve.src, ""))
            dst_val = str(self.state.ctx.get(valve.dst, ""))
            
            pressure = len(src_val)
            
            # Logic: If source pressure exceeds threshold, 'fluid' flows to destination
            if pressure >= valve.pressure_threshold:
                logger.warning(f"💧 [FLOW] Valve '{valve.name}' opened! Pressure {pressure} >= {valve.pressure_threshold}")
                
                # Transfer part of the 'fluid' (text content)
                # Mock flow: append a snippet or summarized version
                flow_snippet = f"\n[INFLOW FROM {valve.src}]: {src_val[:50]}..."
                
                if flow_snippet not in dst_val:
                    self.state.ctx[valve.dst] = dst_val + flow_snippet
                    changes_occurred = True
            else:
                logger.info(f"░ [STAGNANT] Valve '{valve.name}': Pressure {pressure} too low.")
                
        return changes_occurred

if __name__ == "__main__":
    # Standalone verification
    logging.basicConfig(level=logging.INFO)
    state = TOAMachineState()
    circuit = FluidicCircuit(state)
    
    # Setup: Data only flows to 'ctx2' if 'ctx1' is "pressurized" (long enough)
    circuit.add_valve(Valve("Trust_Filter", src="1", dst="2", pressure_threshold=20))
    
    print("\n[Step 1] Low Pressure")
    state.ctx["1"] = "Short"
    circuit.pump_cycle()
    print(f"Ctx 2: {state.ctx.get('2', 'Empty')}")
    
    print("\n[Step 2] High Pressure")
    state.ctx["1"] = "This is a very long string that should trigger the valve."
    circuit.pump_cycle()
    print(f"Ctx 2: {state.ctx.get('2')}")
