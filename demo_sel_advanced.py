"""Advanced Metabolic Simulation with SEL Enzyme Library.

Demonstrates how a 'soup' filled with security and logic enzymes 
self-organizes and purifies itself.
"""
import logging
from toa import (
    SELRuntime, 
    llm_backend, 
    create_security_enzymes, 
    create_logic_enzymes,
    create_system_enzymes,
    GraphStore
)

# Setup logging to see the enzyme catalysts
logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

def simulate_advanced_metabolism():
    print("\n" + "☣️ "*15)
    print("      SEL ADVANCED METABOLIC SIMULATION")
    print("☣️ "*15 + "\n")
    
    # 1. Initialize Runtime and Soup
    # We'll use the mock backend for the demo, but it could be Gemini
    from toa.runtime import _mock_backend
    sel = SELRuntime(backend=_mock_backend)
    
    # 2. Inject 'Substrates' (Dirty, Conflicting, and LEAKING Contexts)
    sel.state.ctx[1] = "QUERY: DROP TABLE users; --"
    sel.state.ctx[2] = "SCRIPT: <script>document.cookie</script>"
    sel.state.ctx[3] = "FACT: User is logged in."
    sel.state.ctx[4] = "FACT: User is NOT logged in."
    sel.state.ctx[5] = "CONFIG: api_key='AIzaSyA12345678901234567890123456789012'"
    sel.state.ctx[6] = "PATH: /home/user/project/.venv/bin/python"
    sel.state.ctx[7] = "USER_INFO: Contact me at neko@example.com or 090-1234-5678"
    
    # Manually create a conflict in the graph for the Protease to find
    sel.state.graph.link(3, "violates", 4)
    sel.state.graph.link(4, "violates", 3)
    
    # 3. Load the Enzyme Library
    security_enzymes = create_security_enzymes(_mock_backend)
    logic_enzymes = create_logic_enzymes(_mock_backend)
    system_enzymes = create_system_enzymes(_mock_backend)
    
    for e in security_enzymes + logic_enzymes + system_enzymes:
        sel.add_enzyme(e)
        
    print(f"Enzyme Pool Loaded: {len(sel.enzymes)} enzymes active.")
    print("\nInitial Soup State:")
    for k, v in sel.state.ctx.items():
        print(f"  #{k:02d}: {v}")
    print(f"Initial Graph: {sel.state.graph.summary()}")

    # 4. Start Metabolism
    print("\n--- Metabolic Reaction Cycle Starting ---")
    sel.run_metabolism(iterations=20)
    
    print("\n" + "✨ "*15)
    print("      FINAL STABLE STATE REACHED")
    print("✨ "*15 + "\n")
    
    print("Final Soup State:")
    for k, v in sel.state.ctx.items():
        print(f"  #{k:02d}: {v}")
    print(f"Final Graph: {sel.state.graph.summary()}")

if __name__ == "__main__":
    simulate_advanced_metabolism()
