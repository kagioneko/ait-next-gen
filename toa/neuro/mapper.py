"""NeuroState → TOA ctx register mapping + emotion Dictionary"""
from ..dictionary import Dictionary, default_dictionary
from .loader import NeuroSnapshot

# ── ctx register assignments ──────────────────────────────────────────────────
CTX_TO_DIM: dict[int, str] = {
    1: "desire",
    2: "sorrow",
    3: "calm",
    4: "openness",
    5: "guilt",
    6: "euphoria",
    7: "corruption",
}

DIM_TO_CTX: dict[str, int] = {v: k for k, v in CTX_TO_DIM.items()}

# ── CPL rules (src_ctx, edge_type, dst_ctx, description) ─────────────────────
# Structural rules: always applied
CPL_STRUCTURAL = [
    (6, "creates",  4, "euphoria creates openness"),
    (4, "requires", 6, "openness requires euphoria"),
    (1, "extends",  6, "desire extends euphoria"),
    (3, "cancels",  2, "calm cancels sorrow"),
    (6, "cancels",  7, "euphoria cancels corruption"),
]

# Conditional conflict rules: (src, violates_dst, threshold_priority, label)
# Applied as: always add `violates`, then IF value > threshold/10 ALSO add `requires`
# → requires + violates on same pair = conflict detected
CPL_PARADOX = [
    (2, 3, 3, "sorrow ⟂ calm      (> 0.3 → paradox)"),
    (5, 1, 2, "guilt  ⟂ desire    (> 0.2 → paradox)"),
    (7, 4, 1, "corruption ⟂ openness (> 0.1 → paradox)"),
]

CPL_RULES = CPL_STRUCTURAL + [
    (src, "violates", dst, lbl) for src, dst, _, lbl in CPL_PARADOX
]


# ── Emotion Dictionary ────────────────────────────────────────────────────────

def build_neuro_dictionary(snapshot: NeuroSnapshot = None) -> Dictionary:
    """Return a Dictionary with emotion domain + native handlers.

    - domain 'e' = emotion
    - action 'l' = load  : reads value from snapshot into ctx[N]
    - action 't' = threshold : checks ctx[N] > priority/10, preserves ctx[N]
    """
    d = default_dictionary()
    d.add_domain('e', 'emotion', 'NeuroState emotion layer')

    def _load(domain, action, ctx_id, priority, ctx_data):
        if snapshot is None:
            return None, False, "[NEURO] no snapshot"
        dim = CTX_TO_DIM.get(ctx_id)
        if dim is None:
            return None, False, f"[NEURO] ctx #{ctx_id} not mapped"
        val = snapshot.state[dim]
        return val, True, f"[NEURO] {dim}={val:.4f} → #{ctx_id:02d}"

    def _threshold(domain, action, ctx_id, priority, ctx_data):
        if ctx_data is None:
            return ctx_data, False, f"[NEURO] #{ctx_id:02d} empty"
        thresh = priority / 10.0
        ok = float(ctx_data) > thresh
        sym = ">" if ok else "<="
        # Return original ctx_data so the value is preserved in ctx
        return ctx_data, ok, f"[NEURO] #{ctx_id:02d} {ctx_data:.4f} {sym} {thresh:.1f}"

    d.add_action('l', 'load',      'Load emotion value from snapshot',  handler=_load)
    d.add_action('t', 'threshold', 'Check emotion > threshold, preserve ctx', handler=_threshold)
    return d
