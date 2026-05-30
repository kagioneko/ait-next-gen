"""Real-data security scan demo

Injects actual vulnerable code into TOA #ctx registers,
then runs the scan pipeline. Claude analyzes the real code
and returns 0 (vuln found) or 1 (clean) per instruction.

Usage:
    python -m toa.demo_real_scan
    TOA_BACKEND=mock python -m toa.demo_real_scan
"""
import os
import sys
import textwrap
from pathlib import Path

# Allow running as script or module
sys.path.insert(0, str(Path(__file__).parent.parent))

from toa import TOAMachine
from toa.runtime import llm_backend
from toa.transpiler import compile_program

# ── test payloads ─────────────────────────────────────────────────────────────

SAMPLES = {
    "xss_vulnerable": textwrap.dedent("""\
        // user profile page
        function renderProfile(username) {
            document.getElementById('name').innerHTML = username;
        }
        const user = getQueryParam('user');
        renderProfile(user);
    """),

    "sqli_vulnerable": textwrap.dedent("""\
        def get_user(username):
            query = "SELECT * FROM users WHERE name = '" + username + "'"
            return db.execute(query)
    """),

    "both_vulnerable": textwrap.dedent("""\
        app.get('/search', (req, res) => {
            const q = req.query.q;
            db.query("SELECT * FROM items WHERE name='" + q + "'", (err, rows) => {
                res.send('<h1>Results for: ' + q + '</h1>');
            });
        });
    """),

    "clean": textwrap.dedent("""\
        import { escape } from 'html-escaper';
        import db from './db.js';

        app.get('/search', async (req, res) => {
            const q = req.query.q ?? '';
            const rows = await db.query(
                'SELECT * FROM items WHERE name = $1', [q]
            );
            res.send('<h1>Results for: ' + escape(q) + '</h1>');
        });
    """),
}

# ── tape ──────────────────────────────────────────────────────────────────────

TAPE_SRC = (Path(__file__).parent / "demo_real_scan.lisp").read_text()

# ── runner ────────────────────────────────────────────────────────────────────

_SEP = "─" * 60


def run_scan(name: str, code: str, verbose: bool = True) -> dict:
    tape = compile_program(TAPE_SRC)

    machine = TOAMachine(backend=llm_backend, verbose=verbose)
    state = machine.run.__func__  # get unbound method

    # Pre-inject: write code into #01 before execution starts
    from toa.packet import tokenize
    from toa.machine import TOAMachineState

    packets = tokenize(tape)
    st = TOAMachineState()
    st.ctx[1] = code          # inject real code into #01

    # patch machine to use pre-seeded state
    result_state = machine._execute(packets, st)

    return {
        "name": name,
        "ctx": dict(result_state.ctx),
        "stack": result_state.stack,
        "graph": result_state.graph,
    }


def print_result(r: dict):
    print(f"\n{'═'*60}")
    print(f"  Sample  : {r['name']}")
    print(f"  Stack   : {r['stack']}")

    ctx = r["ctx"]
    xss_result  = ctx.get(2, "—")
    sqli_result = ctx.get(3, "—")
    fixed_code  = ctx.get(4)

    print(f"  XSS  #02: {str(xss_result)[:80]}")
    print(f"  SQLi #03: {str(sqli_result)[:80]}")
    if fixed_code:
        print(f"  Fix  #04: {str(fixed_code)[:120]}")
    print(f"  Final#09: {ctx.get(9, '—')}")


def main():
    samples = list(SAMPLES.items())

    # default: run all samples
    names = sys.argv[1:] if len(sys.argv) > 1 else list(SAMPLES.keys())

    for name in names:
        if name not in SAMPLES:
            print(f"Unknown sample '{name}'. Choose from: {list(SAMPLES.keys())}")
            continue

        code = SAMPLES[name]
        print(f"\n{_SEP}")
        print(f"[SCAN] {name}")
        print(_SEP)
        print("Input code:")
        for line in code.splitlines():
            print(f"  {line}")
        print(_SEP)

        r = run_scan(name, code, verbose=True)
        print_result(r)


if __name__ == "__main__":
    main()
