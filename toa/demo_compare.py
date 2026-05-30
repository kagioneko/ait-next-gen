"""Multi-backend comparison demo

Runs the same TOA tape against multiple LLM backends and
shows side-by-side what each one said per packet.

Usage:
    python -m toa.demo_compare                     # claude_cli vs codex_cli
    python -m toa.demo_compare --backends claude_cli codex_cli gemini_api
    python -m toa.demo_compare --sample sqli_vulnerable
"""
import argparse
import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from toa.machine import TOAMachine, MachineHooks
from toa.packet import tokenize
from toa.machine import TOAMachineState
from toa.runtime import _BACKENDS
from toa.transpiler import compile_program

# ── reuse samples from demo_real_scan ────────────────────────────────────────
from toa.demo_real_scan import SAMPLES, TAPE_SRC

# ── per-backend trace collector ───────────────────────────────────────────────

class TraceCollector(MachineHooks):
    def __init__(self): self.lines = []
    def on_exec(self, domain, action, ctx_id, priority, value, success):
        self.lines.append((domain, action, ctx_id, priority, value, success))

# ── runner ────────────────────────────────────────────────────────────────────

def run_one(backend_name: str, code: str, verbose: bool = False):
    backend_fn = _BACKENDS[backend_name]
    collector = TraceCollector()
    machine = TOAMachine(backend=backend_fn, hooks=collector, verbose=verbose)
    tape = compile_program(TAPE_SRC)
    packets = tokenize(tape)
    state = TOAMachineState()
    state.ctx[1] = code
    machine._execute(packets, state)
    return state, collector

# ── pretty print ──────────────────────────────────────────────────────────────

_COL = 46  # column width per backend

def _truncate(s, n): return s if len(s) <= n else s[:n-1] + "…"

def compare(sample_name: str, backends: list[str]):
    code = SAMPLES[sample_name]
    print(f"\n{'═'*80}")
    print(f"  Sample: {sample_name}")
    print(f"{'═'*80}")
    print("Input code:")
    for line in code.strip().splitlines():
        print(f"  {line}")
    print()

    results = {}
    for b in backends:
        print(f"  ► Running {b}...", flush=True)
        state, collector = run_one(b, code)
        results[b] = {"state": state, "trace": collector.lines}

    # header
    header = "  {:20s}".format("packet")
    for b in backends:
        header += f"  {b:{_COL}s}"
    print(f"\n{header}")
    print("  " + "─" * (22 + len(backends) * (_COL + 2)))

    # per-exec comparison
    max_execs = max(len(r["trace"]) for r in results.values())
    for i in range(max_execs):
        rows = {}
        for b in backends:
            tr = results[b]["trace"]
            rows[b] = tr[i] if i < len(tr) else None

        # use first backend's packet label
        first = next(r for r in rows.values() if r)
        label = f"{first[0][0]}{first[2]:x}{first[1][0]}{first[3]}"
        row = f"  {label:20s}"
        for b in backends:
            r = rows[b]
            if r:
                ok_mark = "✓" if r[5] else "✗"
                msg = _truncate(str(r[4])[:_COL-4], _COL-4)
                row += f"  {ok_mark} {msg:{_COL-3}s}"
            else:
                row += f"  {'—':{_COL}s}"
        print(row)

    # final verdict
    print()
    for b in backends:
        st = results[b]["state"]
        print(f"  {b:20s}  stack={st.stack}  ctx_keys={sorted(st.ctx.keys())}")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--sample", default="sqli_vulnerable",
                        choices=list(SAMPLES.keys()))
    parser.add_argument("--backends", nargs="+",
                        default=["claude_cli", "codex_cli"])
    parser.add_argument("--all-samples", action="store_true")
    args = parser.parse_args()

    available = list(_BACKENDS.keys())
    for b in args.backends:
        if b not in available:
            print(f"Unknown backend '{b}'. Choose from: {available}")
            sys.exit(1)

    samples = list(SAMPLES.keys()) if args.all_samples else [args.sample]
    for s in samples:
        compare(s, args.backends)


if __name__ == "__main__":
    main()
