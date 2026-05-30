"""TOA Tape Generator — LLMがNeuroState感情状態からAIT-Lispテープを自己生成する

Flow:
  NeuroSnapshot → prompt → LLM(claude CLI) → AIT-Lisp source
      → compile_program → compiled tape → TOAMachine → 実行結果
"""
from __future__ import annotations
import subprocess
from typing import Optional

from ..transpiler import compile_program, CompileError
from ..machine import TOAMachine
from .loader import NeuroSnapshot
from .mapper import DIM_TO_CTX, build_neuro_dictionary


_SYSTEM_PROMPT = """\
You are a TOA (Tape-Oriented Assembly) emotion tape generator.

TOA AIT-Lisp syntax rules:
  (def domain e emotion)         ; register 'e' as emotion domain
  (def action l load)            ; register 'l' as load action
  (def action t threshold)       ; register 't' as threshold action
  (e N l 5)                      ; load emotion ctx#N from snapshot (N=1-7)
  (e N t P)                      ; threshold: ctx#N > P/10? (preserves ctx value)
  (link SRC TYPE DST)            ; CPL edge (TYPE: creates/requires/violates/cancels/extends)
  (if (e N t P) (link A B C))    ; conditional CPL edge
  (do E1 E2 ...)                 ; sequential execution

NeuroState ctx register mapping:
  #01=desire  #02=sorrow  #03=calm  #04=openness
  #05=guilt   #06=euphoria  #07=corruption

Conflict detection: when the same (src, dst) pair has BOTH 'requires' AND 'violates' edges,
the CPL graph detects a conflict. Use conditional (if) to add 'requires' only when the
emotion threshold is exceeded.

You will receive a NeuroState snapshot. Generate a TOA AIT-Lisp tape that:
1. Defines the emotion domain and actions (if not standard)
2. Loads the ACTIVE (high-value) emotions into ctx
3. Builds a CPL graph reflecting how these emotions interact
4. Conditionally detects paradox/conflict states using (if (e N t P) (link ...))
5. May include any creative emotional logic you see fit

Reply ONLY with valid AIT-Lisp code. No markdown fences. No explanation. No comments beyond short ; inline notes.
"""


def generate_tape(
    snapshot: NeuroSnapshot,
    run_result: bool = True,
    verbose: bool = False,
) -> dict:
    """Ask LLM to generate a TOA AIT-Lisp tape for the given snapshot.

    Returns:
        {
          "lisp": str,          # raw LLM output
          "tape": str | None,   # compiled tape (None if compile failed)
          "error": str | None,  # compile error message
          "exec_state": ...     # TOAMachineState if run_result=True
        }
    """
    state_lines = "\n".join(
        f"  #{DIM_TO_CTX[dim]:02d} {dim:<12} = {val:.4f}"
        for dim, val in sorted(snapshot.state.items(), key=lambda x: x[1], reverse=True)
    )
    prompt = (
        f"NeuroState snapshot [{snapshot.timestamp[:16]}]:\n"
        f"{state_lines}\n\n"
        "Generate a TOA AIT-Lisp tape for this emotion state."
    )

    try:
        proc = subprocess.run(
            ["claude", "--system-prompt", _SYSTEM_PROMPT, "-p", prompt],
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode != 0:
            return {"lisp": "", "tape": None, "error": proc.stderr.strip()[:300], "exec_state": None}
        lisp_src = proc.stdout.strip()
    except Exception as e:
        return {"lisp": "", "tape": None, "error": str(e), "exec_state": None}

    try:
        tape = compile_program(lisp_src)
    except (CompileError, SyntaxError) as e:
        return {"lisp": lisp_src, "tape": None, "error": f"CompileError: {e}", "exec_state": None}

    exec_state = None
    if run_result:
        d = build_neuro_dictionary(snapshot)
        machine = TOAMachine(dictionary=d, backend=_noop_backend, verbose=verbose)
        exec_state = machine.run(tape)

    return {"lisp": lisp_src, "tape": tape, "error": None, "exec_state": exec_state}


def _noop_backend(domain, action, ctx_id, priority, ctx_data):
    return None, False, f"[TAPEGEN] unhandled: {domain}{action}"
