"""Emotional Drift Loop — 感情状態をLLMがN回再解釈し続ける

同じ NeuroState スナップショットを起点に、前の反復で見つかったCPL知識を
次の反復の入力に追加していく。LLMの解釈がどう収束・発散するかを観察する。

Flow (各 iteration):
  snapshot + 前回までの graph_context → LLM → AIT-Lisp
      → compile → TOAMachine → conflicts + graph
      → summary を次の iteration に引き継ぐ
"""
from __future__ import annotations
import os
import re
import subprocess
from dataclasses import dataclass, field
from typing import List, Optional

from ..transpiler import compile_program, CompileError
from ..machine import TOAMachine, TOAMachineState
from .loader import NeuroSnapshot
from .mapper import DIM_TO_CTX, build_neuro_dictionary


# ── system prompt ─────────────────────────────────────────────────────────────

_SYSTEM = """\
You are a TOA emotion tape generator working in iterative refinement mode.

TOA AIT-Lisp syntax (IMPORTANT: do NOT include (def ...) lines — already registered):
  (e N l 5)                      ; load emotion ctx#N (N=1-7)
  (e N t P)                      ; ctx#N > P/10? (preserves ctx value)
  (link SRC TYPE DST)            ; CPL edge: creates/requires/violates/cancels/extends
  (if (e N t P) (link A B C))    ; conditional edge
  (do E1 E2 ...)                 ; sequential

NeuroState ctx: #01=desire #02=sorrow #03=calm #04=openness #05=guilt #06=euphoria #07=corruption

Conflict = same (src,dst) pair has BOTH requires AND violates edges.

You will receive:
1. The base emotion snapshot (fixed — same every iteration)
2. What previous iterations discovered (accumulated CPL context)

Your goal each iteration: generate a tape that BUILDS ON and REFINES previous findings.
- If a conflict was found: explore WHY it exists, or try to resolve it
- If stable: probe deeper tensions that might not have surfaced yet
- Each iteration should add new insight, not just repeat what was found

Reply ONLY with valid AIT-Lisp. No markdown. No explanation. Short ; inline comments OK.
"""


# ── result per iteration ──────────────────────────────────────────────────────

@dataclass
class IterResult:
    iteration: int
    lisp: str
    tape: Optional[str]
    error: Optional[str]
    exec_state: Optional[TOAMachineState]
    conflicts: list = field(default_factory=list)
    graph_summary: str = ""
    dominant: list = field(default_factory=list)

    def to_context(self) -> str:
        """次のイテレーションへ引き継ぐコンテキスト文字列を生成する。"""
        lines = [f"=== Iteration {self.iteration} findings ==="]
        if self.error:
            lines.append(f"  ERROR: {self.error}")
            return "\n".join(lines)
        lines.append(f"  graph: {self.graph_summary}")
        dom = ", ".join(f"{d}={v:.3f}" for d, v in self.dominant)
        lines.append(f"  dominant: {dom}")
        if self.conflicts:
            for c in self.conflicts:
                lines.append(f"  ⚡ conflict: {c.reason}  ({c.edge_a} × {c.edge_b})")
        else:
            lines.append("  ✓ stable (no conflicts)")
        return "\n".join(lines)

    def summary(self) -> str:
        lines = [f"\n── Iteration {self.iteration} ──"]
        if self.error:
            lines.append(f"  ✗ {self.error}")
            return "\n".join(lines)
        lines.append(self.lisp)
        lines.append(f"\n  → {self.graph_summary}")
        for c in self.conflicts:
            lines.append(f"  ⚡ {c.reason}")
        if not self.conflicts:
            dom = "  ".join(f"{d}={v:.3f}" for d, v in self.dominant)
            lines.append(f"  ✓ stable  dominant: {dom}")
        return "\n".join(lines)


# ── LLM call (backend-agnostic) ───────────────────────────────────────────────

def _strip_fences(text: str) -> str:
    """```lisp ... ``` や ``` ... ``` のmarkdownフェンスを除去する。"""
    text = text.strip()
    m = re.match(r'^```(?:lisp|scheme|)?\s*([\s\S]+?)\s*```$', text)
    return m.group(1).strip() if m else text


def _call_llm(prompt: str, backend: str) -> str:
    if backend == "claude_cli":
        try:
            proc = subprocess.run(
                ["claude", "--system-prompt", _SYSTEM, "-p", prompt],
                capture_output=True, text=True, timeout=90,
            )
            return _strip_fences(proc.stdout) if proc.returncode == 0 else f"; [ERROR] {proc.stderr.strip()[:200]}"
        except Exception as e:
            return f"; [ERROR] {e}"

    elif backend == "gemini_cli":
        combined = f"{_SYSTEM}\n\n{prompt}"
        try:
            proc = subprocess.run(
                ["gemini", "--approval-mode", "plan", "-o", "text", "-p", combined],
                capture_output=True, text=True, timeout=90,
            )
            raw = re.sub(r'\x1b\[[0-9;]*m', '', proc.stdout).strip()
            return _strip_fences(raw) if proc.returncode == 0 else f"; [ERROR] {proc.stderr.strip()[:200]}"
        except Exception as e:
            return f"; [ERROR] {e}"

    else:
        return f"; [ERROR] unknown backend: {backend}"


# ── single iteration ──────────────────────────────────────────────────────────

def _run_iter(
    n: int,
    snap: NeuroSnapshot,
    accumulated_ctx: str,
    backend: str,
    verbose: bool,
) -> IterResult:
    state_lines = "\n".join(
        f"  #{DIM_TO_CTX[dim]:02d} {dim:<12} = {val:.4f}"
        for dim, val in sorted(snap.state.items(), key=lambda x: x[1], reverse=True)
    )

    prompt = f"Base snapshot [{snap.timestamp[:16]}]:\n{state_lines}\n"
    if accumulated_ctx:
        prompt += f"\nPrevious iterations:\n{accumulated_ctx}\n"
    prompt += f"\nIteration {n}: generate your tape."

    lisp = _call_llm(prompt, backend)

    if lisp.lstrip().startswith("; [ERROR]"):
        return IterResult(iteration=n, lisp=lisp, tape=None, error=lisp)

    try:
        tape = compile_program(lisp)
    except (CompileError, SyntaxError) as e:
        # リトライ: "(link) src and dst must be integers" は LLM が変数名を使った場合が多い
        retry_prompt = (
            f"{prompt}\n\n"
            f"PREVIOUS ATTEMPT FAILED with: {e}\n"
            "IMPORTANT: (link SRC TYPE DST) — SRC and DST must be plain integers (1-7), not variable names.\n"
            "Correct: (link 2 violates 3)\n"
            "Wrong:   (link sorrow violates calm)\n"
            "Please try again."
        )
        lisp = _call_llm(retry_prompt, backend)
        if lisp.lstrip().startswith("; [ERROR]"):
            return IterResult(iteration=n, lisp=lisp, tape=None, error=lisp, exec_state=None)
        try:
            tape = compile_program(lisp)
        except (CompileError, SyntaxError) as e2:
            return IterResult(iteration=n, lisp=lisp, tape=None, error=str(e2), exec_state=None)

    d = build_neuro_dictionary(snap)
    machine = TOAMachine(dictionary=d, backend=_noop, verbose=verbose)
    state = machine.run(tape)

    conflicts = state.graph.conflicts()
    dominant = snap.dominant(top=3)

    return IterResult(
        iteration=n,
        lisp=lisp,
        tape=tape,
        error=None,
        exec_state=state,
        conflicts=conflicts,
        graph_summary=state.graph.summary().strip(),
        dominant=dominant,
    )


def _noop(domain, action, ctx_id, priority, ctx_data):
    return None, False, f"[LOOP] unhandled: {domain}{action}"


# ── main loop ─────────────────────────────────────────────────────────────────

def run_loop(
    snap: NeuroSnapshot,
    iterations: int = 3,
    backend: str = "claude_cli",
    verbose: bool = False,
) -> List[IterResult]:
    """感情ドリフトループを実行する。

    Args:
        snap: 起点となるNeuroStateスナップショット
        iterations: 反復回数
        backend: "claude_cli" or "gemini_cli"
        verbose: TOA実行ログを表示するか

    Returns:
        各iterationのIterResultリスト
    """
    results: List[IterResult] = []
    accumulated_ctx = ""

    for n in range(iterations):
        print(f"  [iter {n}] calling {backend}…", flush=True)
        r = _run_iter(n, snap, accumulated_ctx, backend, verbose)
        results.append(r)

        # 次のiterへコンテキストを引き継ぐ
        accumulated_ctx += r.to_context() + "\n\n"

    return results
