"""AIT-Lisp → TOA transpiler

Converts S-expression programs into TOA tape strings.

Supported forms:
  (s 4 x 9)              → s4x9          EXEC
  (load 4)               → ##04          CTX_LOAD
  (push 4)               → >>04          CTX_PUSH
  (link 1 creates 3)     → #01 =>creates=> #03   CPL edge
  (def domain n neuro)   → def:[d:n:neuro]
  (def action f fix)     → def:[a:f:fix]
  (do e1 e2 ...)         → e1\\ne2\\n...  sequential
  (if cond then)         → cond + JIF (skip then if false)
  (if cond then else)    → cond + JIF + then + JMP + else
  (repeat N body)        → body repeated N times (compile-time unroll)
"""
from __future__ import annotations
import re
import sys
from typing import Any, List, Optional


# ── S-expression parser (reused from ait_eval.py) ────────────────────────────

class Symbol(str):
    pass


def _parse(program: str) -> Any:
    # strip line comments before tokenizing so '(' inside comments don't leak
    clean = '\n'.join(line.split(';')[0] for line in program.splitlines())
    tokens = re.findall(r'\(|\)|[^\s()]+', clean)

    def read(tokens):
        if not tokens:
            raise SyntaxError("Unexpected end of input")
        tok = tokens.pop(0)
        if tok == '(':
            lst = []
            while tokens and tokens[0] != ')':
                lst.append(read(tokens))
            if not tokens:
                raise SyntaxError("Missing closing ')'")
            tokens.pop(0)
            return lst
        if tok == ')':
            raise SyntaxError("Unexpected ')'")
        try:
            return int(tok)
        except ValueError:
            return Symbol(tok)

    results = []
    while tokens:
        results.append(read(tokens))
    return results  # list of top-level expressions


# ── ctx / priority helpers ────────────────────────────────────────────────────

_HEX = '0123456789abcdef'


def _ctx_char(n: int) -> str:
    if not (0 <= n <= 15):
        raise ValueError(f"ctx id must be 0-15, got {n}")
    return _HEX[n]


def _priority_char(n: int) -> str:
    if not (0 <= n <= 9):
        raise ValueError(f"priority must be 0-9, got {n}")
    return str(n)


# CPL edge types that use '=>' vs '=='
_ARROW_TYPES = {"creates", "extends"}


def _cpl_arrow(edge_type: str) -> str:
    return "=>" if edge_type in _ARROW_TYPES else "=="


# ── compiler ─────────────────────────────────────────────────────────────────

class CompileError(Exception):
    pass


def _compile_expr(expr: Any) -> List[str]:
    """Compile a single expression to a list of TOA token strings."""

    # ── atom (bare packet string, e.g. already-written "s4x9") ──────────
    if isinstance(expr, str):
        return [expr]

    if not isinstance(expr, list) or len(expr) == 0:
        raise CompileError(f"Cannot compile: {expr!r}")

    head = expr[0]

    # ── EXEC: (domain ctx_int action priority_int) ───────────────────────
    # head is a single letter domain and the list has exactly 4 elements
    if (isinstance(head, Symbol) and len(head) == 1
            and len(expr) == 4
            and isinstance(expr[1], int)
            and isinstance(expr[2], Symbol) and len(expr[2]) == 1
            and isinstance(expr[3], int)):
        domain  = str(head)
        ctx     = _ctx_char(expr[1])
        action  = str(expr[2])
        priority = _priority_char(expr[3])
        return [f"{domain}{ctx}{action}{priority}"]

    # ── (do e1 e2 ...) ───────────────────────────────────────────────────
    if head == Symbol('do'):
        pkts = []
        for sub in expr[1:]:
            pkts.extend(_compile_expr(sub))
        return pkts

    # ── (if cond then [else]) ────────────────────────────────────────────
    if head == Symbol('if'):
        if len(expr) not in (3, 4):
            raise CompileError(f"(if) requires 2 or 3 args, got {len(expr)-1}")
        cond_pkts = _compile_expr(expr[1])
        then_pkts = _compile_expr(expr[2])
        else_pkts = _compile_expr(expr[3]) if len(expr) == 4 else []

        result = list(cond_pkts)
        # JIF skips: entire then block + the trailing JMP (if else exists)
        skip_then = len(then_pkts) + (1 if else_pkts else 0)
        result.append(f"?b{skip_then:02x}")
        result.extend(then_pkts)
        if else_pkts:
            result.append(f"!{len(else_pkts):03x}")
            result.extend(else_pkts)
        return result

    # ── (load ctx_int) → ##NN ────────────────────────────────────────────
    if head == Symbol('load'):
        if len(expr) != 2 or not isinstance(expr[1], int):
            raise CompileError(f"(load N) expects one integer, got {expr[1:]}")
        return [f"##{expr[1]:02x}"]

    # ── (push ctx_int) → >>NN ────────────────────────────────────────────
    if head == Symbol('push'):
        if len(expr) != 2 or not isinstance(expr[1], int):
            raise CompileError(f"(push N) expects one integer, got {expr[1:]}")
        return [f">>{expr[1]:02x}"]

    # ── (jmp offset) → !NNN ──────────────────────────────────────────────
    if head == Symbol('jmp'):
        if len(expr) != 2 or not isinstance(expr[1], int):
            raise CompileError(f"(jmp N) expects one integer")
        return [f"!{expr[1]:03x}"]

    # ── (jif offset) → ?bNN ──────────────────────────────────────────────
    if head == Symbol('jif'):
        if len(expr) != 2 or not isinstance(expr[1], int):
            raise CompileError(f"(jif N) expects one integer")
        return [f"?b{expr[1]:02x}"]

    # ── (link src edge_type dst) → CPL edge line ─────────────────────────
    if head == Symbol('link'):
        if len(expr) != 4:
            raise CompileError(f"(link src type dst) expects 3 args")
        src, edge_type, dst = expr[1], str(expr[2]), expr[3]
        if not isinstance(src, int) or not isinstance(dst, int):
            raise CompileError(f"(link) src and dst must be integers")
        arrow = _cpl_arrow(edge_type)
        return [f"#{src:02d} {arrow}{edge_type}=> #{dst:02d}"]

    # ── (def domain char name) / (def action char name) ──────────────────
    if head == Symbol('def'):
        if len(expr) != 4:
            raise CompileError(f"(def domain|action char name) expects 3 args")
        kind, char, name = str(expr[1]), str(expr[2]), str(expr[3])
        if kind not in ('domain', 'action'):
            raise CompileError(f"(def) first arg must be 'domain' or 'action'")
        k = 'd' if kind == 'domain' else 'a'
        return [f"def:[{k}:{char}:{name}]"]

    # ── (repeat N body) → compile-time unroll ────────────────────────────
    if head == Symbol('repeat'):
        if len(expr) != 3 or not isinstance(expr[1], int):
            raise CompileError(f"(repeat N body) expects integer count")
        count = expr[1]
        body_pkts = _compile_expr(expr[2])
        return body_pkts * count

    raise CompileError(f"Unknown form: {head!r}")


def compile_program(source: str) -> str:
    """Compile a multi-expression AIT-Lisp program to a TOA tape string."""
    exprs = _parse(source)
    all_pkts: List[str] = []
    for expr in exprs:
        all_pkts.extend(_compile_expr(expr))
    return "\n".join(all_pkts)


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    import argparse

    parser = argparse.ArgumentParser(
        prog="python -m toa.transpiler",
        description="Compile AIT-Lisp source to a TOA tape",
    )
    parser.add_argument("source", nargs="?", help="path to .lisp file (stdin if omitted)")
    parser.add_argument("-o", "--out", help="output file (stdout if omitted)")
    parser.add_argument("--run", action="store_true", help="also run the compiled tape")
    parser.add_argument("--backend", default=None,
                        help="TOA_BACKEND override (claude_cli / anthropic_api / mock)")
    args = parser.parse_args()

    if args.source:
        src = open(args.source).read()
    else:
        src = sys.stdin.read()

    try:
        tape = compile_program(src)
    except (CompileError, SyntaxError) as e:
        print(f"Compile error: {e}", file=sys.stderr)
        sys.exit(1)

    if args.out:
        open(args.out, 'w').write(tape + "\n")
        print(f"[transpiler] written to {args.out}", file=sys.stderr)
    else:
        print(tape)

    if args.run:
        import os
        if args.backend:
            os.environ["TOA_BACKEND"] = args.backend
        from .machine import TOAMachine
        from .runtime import llm_backend
        print("\n--- running compiled tape ---", file=sys.stderr)
        machine = TOAMachine(backend=llm_backend, verbose=True)
        state = machine.run(tape)
        print(f"\n[DONE] stack={state.stack}", file=sys.stderr)


if __name__ == "__main__":
    main()
