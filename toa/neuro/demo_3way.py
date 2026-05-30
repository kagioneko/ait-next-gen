"""NeuroState × TOA — 3バックエンド比較デモ

同じ感情スナップショットに対して Claude / Gemini(Antigravity) / Codex が
それぞれどんな AIT-Lisp テープを自己生成するかを比較する。

Usage:
    python -m toa.neuro.demo_3way                         # 最新スナップショット
    python -m toa.neuro.demo_3way --backends claude_cli gemini_cli codex_cli
    python -m toa.neuro.demo_3way --snapshot-index 2     # 直近3件目
"""
from __future__ import annotations
import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from toa.neuro.loader import load_snapshots, NeuroSnapshot
from toa.neuro.mapper import DIM_TO_CTX, build_neuro_dictionary
from toa.transpiler import compile_program, CompileError
from toa.machine import TOAMachine


# ── system prompt (same for all backends) ────────────────────────────────────

_SYSTEM = """\
You are a TOA (Tape-Oriented Assembly) emotion tape generator.

TOA AIT-Lisp syntax:
  (def domain e emotion)    ; emotion domain
  (def action l load)       ; load action
  (def action t threshold)  ; threshold action (priority/10 is the threshold)
  (e N l 5)                 ; load ctx#N from snapshot (N=1-7)
  (e N t P)                 ; ctx#N > P/10? (preserves ctx value, success=bool)
  (link SRC TYPE DST)       ; CPL edge: creates/requires/violates/cancels/extends
  (if (e N t P) (link A B C)) ; conditional edge
  (do E1 E2 ...)            ; sequential

NeuroState ctx mapping:
  #01=desire  #02=sorrow   #03=calm     #04=openness
  #05=guilt   #06=euphoria  #07=corruption

Conflict = same (src,dst) with BOTH requires AND violates.
Use (if (e N t P) (link ...)) to add requires conditionally.

Reply ONLY with valid AIT-Lisp. No markdown. No explanation.
IMPORTANT: do NOT include (def ...) lines — handlers are pre-registered.
"""


# ── per-backend call ──────────────────────────────────────────────────────────

def _call_claude(prompt: str) -> str:
    try:
        proc = subprocess.run(
            ["claude", "--system-prompt", _SYSTEM, "-p", prompt],
            capture_output=True, text=True, timeout=90,
        )
        return proc.stdout.strip() if proc.returncode == 0 else f"; [ERROR] {proc.stderr.strip()[:200]}"
    except Exception as e:
        return f"; [ERROR] {e}"


def _call_gemini(prompt: str) -> str:
    combined = f"{_SYSTEM}\n\n{prompt}"
    try:
        proc = subprocess.run(
            ["gemini", "--approval-mode", "plan", "-o", "text", "-p", combined],
            capture_output=True, text=True, timeout=90,
        )
        raw = re.sub(r'\x1b\[[0-9;]*m', '', proc.stdout).strip()
        return raw if proc.returncode == 0 else f"; [ERROR] {proc.stderr.strip()[:200]}"
    except Exception as e:
        return f"; [ERROR] {e}"


def _call_codex(prompt: str) -> str:
    full = f"{_SYSTEM}\n\n{prompt}"
    try:
        proc = subprocess.run(
            ["codex", "exec", full],
            input="", capture_output=True, text=True, timeout=90,
        )
        raw = proc.stdout.strip()
        # grab the last non-empty block as the response
        return raw if raw else f"; [ERROR] {proc.stderr.strip()[:200]}"
    except Exception as e:
        return f"; [ERROR] {e}"


_CALLERS = {
    "claude_cli": _call_claude,
    "gemini_cli": _call_gemini,
    "codex_cli":  _call_codex,
}


# ── prompt builder ────────────────────────────────────────────────────────────

def _build_prompt(snap: NeuroSnapshot) -> str:
    lines = "\n".join(
        f"  #{DIM_TO_CTX[dim]:02d} {dim:<12} = {val:.4f}"
        for dim, val in sorted(snap.state.items(), key=lambda x: x[1], reverse=True)
    )
    return (
        f"NeuroState snapshot [{snap.timestamp[:16]}]:\n{lines}\n\n"
        "Generate a TOA AIT-Lisp tape for this emotion state.\n"
        "Remember: do NOT include (def ...) lines."
    )


# ── compile + run ─────────────────────────────────────────────────────────────

def _try_run(lisp_src: str, snap: NeuroSnapshot, verbose: bool) -> dict:
    if lisp_src.lstrip().startswith("; [ERROR]"):
        return {"ok": False, "error": lisp_src, "tape": None, "conflicts": [], "stack": []}
    try:
        tape = compile_program(lisp_src)
    except (CompileError, SyntaxError) as e:
        return {"ok": False, "error": f"CompileError: {e}", "tape": None, "conflicts": [], "stack": []}

    d = build_neuro_dictionary(snap)
    machine = TOAMachine(dictionary=d, backend=lambda *a: (None, False, "noop"), verbose=verbose)
    state = machine.run(tape)
    return {
        "ok": True,
        "error": None,
        "tape": tape,
        "conflicts": state.graph.conflicts(),
        "stack": state.stack,
        "graph_summary": state.graph.summary().strip(),
    }


# ── main comparison ───────────────────────────────────────────────────────────

def compare(snap: NeuroSnapshot, backends: list[str], verbose: bool = False):
    prompt = _build_prompt(snap)

    print(f"\n{'═'*70}")
    print(f"  NeuroState 3-way LLM Tape Generation")
    print(f"  {snap}")
    print(f"{'═'*70}")
    print(snap.as_ctx_table())

    results = {}
    for b in backends:
        caller = _CALLERS.get(b)
        if caller is None:
            print(f"  !! unknown backend '{b}'", file=sys.stderr)
            continue
        print(f"\n  ► Calling {b} …", flush=True)
        lisp_src = caller(prompt)
        results[b] = {"lisp": lisp_src, **_try_run(lisp_src, snap, verbose)}

    # ── print results ─────────────────────────────────────────────────────
    for b, r in results.items():
        print(f"\n{'─'*70}")
        print(f"  [{b}]")
        if not r["ok"]:
            print(f"  ✗ {r['error']}")
            continue
        print(r["lisp"])
        print(f"\n  → conflicts: {len(r['conflicts'])}  graph: {r.get('graph_summary','?')}")
        for c in r["conflicts"]:
            print(f"    ⚡ {c}")
        if not r["conflicts"]:
            print("    ✓ 安定状態")

    # ── summary table ─────────────────────────────────────────────────────
    print(f"\n{'═'*70}")
    print(f"  Summary")
    print(f"{'─'*70}")
    for b, r in results.items():
        if r["ok"]:
            n_link = r["tape"].count("=>") + r["tape"].count("==") if r["tape"] else 0
            n_if   = r["tape"].count("?b") if r["tape"] else 0
            n_conf = len(r["conflicts"])
            conf_str = f"⚡ {n_conf} conflicts" if n_conf else "✓ stable"
            print(f"  {b:<16}  lines={r['tape'].count(chr(10)):<3}  "
                  f"links={n_link:<3}  ifs={n_if}  {conf_str}")
        else:
            print(f"  {b:<16}  ✗ error")
    print()


def main():
    parser = argparse.ArgumentParser(
        prog="python -m toa.neuro.demo_3way",
        description="NeuroState × TOA 3-backend LLM tape comparison",
    )
    parser.add_argument("--backends", nargs="+",
                        default=["claude_cli", "gemini_cli", "codex_cli"])
    parser.add_argument("--snapshot-index", "-n", type=int, default=0,
                        help="0=latest, 1=second latest, etc.")
    parser.add_argument("--verbose", "-v", action="store_true")
    args = parser.parse_args()

    n = args.snapshot_index + 1
    snaps = load_snapshots(limit=n)
    if not snaps:
        print("spirit.db にスナップショットが見つかりません", file=sys.stderr)
        sys.exit(1)

    snap = snaps[0]  # already reversed to chronological; index 0 = oldest of the loaded set
    # For "latest" we want the last one
    snap = snaps[-1] if args.snapshot_index == 0 else snaps[0]

    compare(snap, args.backends, verbose=args.verbose)


if __name__ == "__main__":
    main()
