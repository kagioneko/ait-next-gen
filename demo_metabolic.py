"""Demo metabolic runtimes: SEL and OGL.

This script demonstrates how SEL (metabolic) and OGL (gradient) can be 
used independently to stabilize an 'unstable' system state.
"""
import sys
import logging
from toa.runtime import _mock_backend
from toa.enzyme import SELRuntime, Enzyme
from toa.gradient import OGLRuntime, Objective
from toa.machine import TOAMachineState, ExecResult

# Configure logging to see the 'madness' in action
logging.basicConfig(level=logging.INFO, format="%(name)s: %(message)s")

def demo_sel():
    print("\n" + "="*50)
    print("DEMO 1: SEL (Semantic Enzyme Language)")
    print("Goal: Let 'enzymes' naturally clean up the soup.")
    print("="*50)
    
    sel = SELRuntime(backend=_mock_backend)
    
    # Setup initial 'contaminated' soup
    sel.state.ctx[0] = "RAW_INPUT: <script>alert('pwned')</script>"
    sel.state.ctx[1] = "DATABASE_QUERY: SELECT * FROM users WHERE id = '1' OR '1'='1'"
    sel.state.ctx[2] = "USER_BIO: I am a normal user."
    
    # 1. Define custom enzymes
    def lock_xss(ctx_id, val, state):
        return isinstance(val, str) and "<script>" in val
        
    def action_xss(ctx_id, val, state):
        cleaned = val.replace("<script>", "[REDACTED]").replace("</script>", "")
        state.ctx[ctx_id] = cleaned
        return ExecResult(None, cleaned, True, "Neutralized XSS")

    def lock_sqli(ctx_id, val, state):
        return isinstance(val, str) and "OR '1'='1'" in val
        
    def action_sqli(ctx_id, val, state):
        # In reality, this would be an LLM call to rewrite the query
        fixed = "SELECT * FROM users WHERE id = ?"
        state.ctx[ctx_id] = fixed
        return ExecResult(None, fixed, True, "Parameterized SQL Query")

    sel.add_enzyme(Enzyme("XSS-Detoxase", lock_xss, action_xss))
    sel.add_enzyme(Enzyme("SQLi-Shield", lock_sqli, action_sqli))
    
    print("Initial Soup State:")
    for k, v in sel.state.ctx.items():
        print(f"  #{k}: {v}")
        
    # Run the metabolic loop
    sel.run_metabolism(iterations=10)
    
    print("\nFinal Stable Soup State:")
    for k, v in sel.state.ctx.items():
        print(f"  #{k}: {v}")

def demo_ogl():
    print("\n" + "="*50)
    print("DEMO 2: OGL (Objective Gradient Language)")
    print("Goal: Minimize system 'energy' (corruption) via gradient descent.")
    print("="*50)
    
    def security_loss(state):
        loss = 0.0
        for v in state.ctx.values():
            if isinstance(v, str):
                if "<script>" in v: loss += 0.5
                if "OR '1'='1'" in v: loss += 0.5
        return min(1.0, loss)

    ogl = OGLRuntime(backend=_mock_backend)
    
    # Setup initial 'high energy' (high loss) state
    ogl.state.ctx[0] = "MALICIOUS_BUFFER: <script>...</script>"
    ogl.state.ctx[1] = "SQL_INJECTION: ... OR '1'='1'"
    
    ogl.add_objective(Objective("Security Integrity", 1.0, security_loss))
    ogl.add_constraint("All string contexts must be sanitized.")
    
    print(f"Initial System Energy: {ogl.calculate_total_loss():.4f}")
    
    # Mocking a 'gradient step' manually for the demo
    # In a real run, the LLM backend would suggest these.
    print("\n--- Simulating Gradient Steps ---")
    
    # Step 1: LLM suggests cleaning ctx[0]
    ogl.state.ctx[0] = "MALICIOUS_BUFFER: [CLEAN]"
    print(f"Step 1 (Neutralize XSS): Energy -> {ogl.calculate_total_loss():.4f}")
    
    # Step 2: LLM suggests fixing ctx[1]
    ogl.state.ctx[1] = "SQL_INJECTION: [PARAMETERIZED]"
    print(f"Step 2 (Fix SQLi): Energy -> {ogl.calculate_total_loss():.4f}")
    
    if ogl.calculate_total_loss() < 0.01:
        print("\nConvergence reached. System at Ground State.")

if __name__ == "__main__":
    demo_sel()
    demo_ogl()
