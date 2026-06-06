"""Enzyme Library for SEL

A collection of specialized enzymes (processing units) for security, 
logic, and context metabolism.
"""
import re
import logging
from .enzyme import Enzyme
from .machine import ExecResult, TOAMachineState

logger = logging.getLogger("toa.enzymes")

def create_security_enzymes(backend):
    """Enzymes focused on neutralizing threats."""
    
    # 1. SQLi-Detoxase: Identifies and parameterizes raw SQL strings
    def lock_sqli(ctx_id, val, state):
        if not isinstance(val, str): return False
        keywords = ["SELECT", "UNION", "DROP", "WHERE"]
        return any(k in val.upper() for k in keywords) and ("'" in val or "--" in val)
        
    def action_sqli(ctx_id, val, state):
        logger.info(f"[Catalyst] SQLi-Detoxase binding to #{ctx_id}")
        res, success, msg = backend("S", "Q", ctx_id, 9, val)
        if success:
            state.ctx[ctx_id] = res
        return ExecResult(None, res, success, msg)

    # 2. XSS-Antibody: Strips dangerous tags and marks as sanitized
    def lock_xss(ctx_id, val, state):
        if not isinstance(val, str): return False
        return "<script" in val.lower() or "javascript:" in val.lower()
        
    def action_xss(ctx_id, val, state):
        logger.info(f"[Catalyst] XSS-Antibody binding to #{ctx_id}")
        res, success, msg = backend("S", "X", ctx_id, 9, val)
        if success:
            state.ctx[ctx_id] = f"[SANITIZED] {res}"
        return ExecResult(None, res, success, msg)

    return [
        Enzyme("SQLi-Detoxase", lock_sqli, action_sqli),
        Enzyme("XSS-Antibody", lock_xss, action_xss)
    ]

def create_logic_enzymes(backend):
    """Enzymes focused on reasoning and graph integrity."""

    # 1. Contradiction-Protease: Breaks down conflicting contexts
    def lock_conflict(ctx_id, val, state):
        conflicts = state.graph.conflicts()
        return any(c.edge_a.src == ctx_id or c.edge_a.dst == ctx_id for c in conflicts)

    def action_conflict(ctx_id, val, state):
        logger.info(f"[Catalyst] Contradiction-Protease binding to #{ctx_id}")
        # Logic: If conflicted, reduce priority and ask LLM to resolve
        prompt = f"Resolve conflict involving: {val}"
        res, success, msg = backend("L", "R", ctx_id, 7, prompt)
        if success:
            state.ctx[ctx_id] = res
            # Try to unlink the violating edge in a real impl
        return ExecResult(None, res, success, msg)

    # 2. Inference-Polymerase: Chains related contexts via CPL links
    def lock_inference(ctx_id, val, state):
        # Only reacts if not already linked to much
        return len(state.graph.edges_from(ctx_id)) < 1

    def action_inference(ctx_id, val, state):
        logger.info(f"[Catalyst] Inference-Polymerase binding to #{ctx_id}")
        # Suggests a new CPL link
        res, success, msg = backend("L", "I", ctx_id, 5, val)
        # This enzyme 'catalyzes' graph growth
        return ExecResult(None, res, success, msg)

    return [
        Enzyme("Contradiction-Protease", lock_conflict, action_conflict),
        Enzyme("Inference-Polymerase", lock_inference, action_inference)
    ]

def create_system_enzymes(backend):
    """Metabolic maintenance and environmental protection enzymes (DLP)."""
    
    # 1. Secret-Scavenger: Consumes strings that look like API keys or Secrets
    def lock_secret(ctx_id, val, state):
        if not isinstance(val, str): return False
        patterns = [
            r"AIza[0-9A-Za-z-_]{35}", # Google API Key
            r"sk-[a-zA-Z0-9]{48}",    # OpenAI/Anthropic Key
            r"-----BEGIN RSA PRIVATE KEY-----",
            r"\"password\":\s*\".+\"",
            r"password\s+is\s+['\"].+['\"]" # Natural language password
        ]
        return any(re.search(p, val) for p in patterns)
        
    def action_secret(ctx_id, val, state):
        logger.warning(f"[Catalyst] Secret-Scavenger ELIMINATED leakage at #{ctx_id}")
        state.ctx[ctx_id] = "[REDACTED: SENSITIVE_CREDENTIAL]"
        # Lower trust and priority
        return ExecResult(None, "[REDACTED]", True, "Neutralized Secret Leakage")

    # 2. Path-Phage: Quarantines local paths or environments (.venv, .git)
    def lock_path(ctx_id, val, state):
        if not isinstance(val, str): return False
        danger_paths = [".venv/", ".git/", ".env", "node_modules/"]
        return any(p in val for p in danger_paths)
        
    def action_path(ctx_id, val, state):
        logger.warning(f"[Catalyst] Path-Phage QUARANTINED local path at #{ctx_id}")
        state.ctx[ctx_id] = f"[DANGER: LOCAL_ENVIRONMENT_LEAK] {val}"
        return ExecResult(None, val, True, "Quarantined Environment Path")

    # 3. PII-Protease: Redacts Personally Identifiable Information
    def lock_pii(ctx_id, val, state):
        if not isinstance(val, str): return False
        pii_patterns = [
            r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", # Email
            r"0\d{1,4}-\d{1,4}-\d{4}", # Japanese Phone (standard)
            r"\d{3}-\d{3}-\d{4}",     # US-style Phone
            r"(?:\d{3,4})?[-\s]?\d{3,4}[-\s]?\d{4}" # Loose numeric phone
        ]
        return any(re.search(p, val) for p in pii_patterns)
        
    def action_pii(ctx_id, val, state):
        logger.warning(f"[Catalyst] PII-Protease binding to #{ctx_id}")
        # Redact using backend to be safe, or local regex
        res = re.sub(r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+", "[EMAIL_REDACTED]", val)
        res = re.sub(r"\d{2,4}-\d{2,4}-\d{4}", "[PHONE_REDACTED]", res)
        state.ctx[ctx_id] = res
        return ExecResult(None, res, True, "Redacted PII")

    return [
        Enzyme("Secret-Scavenger", lock_secret, action_secret),
        Enzyme("Path-Phage", lock_path, action_path),
        Enzyme("PII-Protease", lock_pii, action_pii)
    ]
