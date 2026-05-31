"""python -m toa.neuro — NeuroState × TOA CLI"""
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(
        prog="python -m toa.neuro",
        description="NeuroState × TOA emotion simulator",
    )
    parser.add_argument("--history", "-n", type=int, default=5,
                        help="Number of snapshots to process (default: 5)")
    parser.add_argument("--verbose", "-v", action="store_true",
                        help="Show full TOA execution trace")
    parser.add_argument("--generate", "-g", action="store_true",
                        help="Ask LLM to self-generate a TOA tape for the latest state")
    parser.add_argument("--loop", "-l", type=int, metavar="N",
                        help="Run emotional drift loop N iterations on the latest snapshot")
    parser.add_argument("--backend", default="claude_cli",
                        choices=["claude_cli", "gemini_cli"],
                        help="LLM backend for --generate / --loop (default: claude_cli)")
    parser.add_argument("--dry-run", action="store_true",
                        help="Print the compiled tape and exit (no execution)")
    args = parser.parse_args()

    from .loader import load_snapshots
    from .simulator import _COMPILED_TAPE, run_simulation

    if args.dry_run:
        print("=== Compiled TOA tape (neuro simulator) ===")
        print(_COMPILED_TAPE)
        return

    print(f"Loading {args.history} snapshots from spirit.db …")
    snapshots = load_snapshots(limit=args.history)
    if not snapshots:
        print("No snapshots found.", file=sys.stderr)
        sys.exit(1)

    print(f"\n=== NeuroState × TOA Simulation ({len(snapshots)} snapshots) ===")
    results = run_simulation(snapshots, verbose=args.verbose)
    for r in results:
        print(r.summary())

    if args.generate:
        from .tape_gen import generate_tape
        latest = snapshots[-1]
        print(f"\n=== LLM Tape Self-Generation ===")
        print(f"Input: {latest}")
        out = generate_tape(latest, run_result=True, verbose=args.verbose)

        if out["error"]:
            print(f"[ERROR] {out['error']}", file=sys.stderr)
            return

        print("\n--- Generated AIT-Lisp ---")
        print(out["lisp"])
        print("\n--- Compiled TOA tape ---")
        print(out["tape"])

        if out["exec_state"]:
            st = out["exec_state"]
            print(f"\n--- Execution result ---")
            print(f"  stack:   {st.stack}")
            print(f"  ctx:     {st.ctx}")
            print(f"  graph:   {st.graph.summary().strip()}")
            if st.graph.conflicts():
                for c in st.graph.conflicts():
                    print(f"  ⚡ {c}")
            else:
                print("  ✓ 安定状態")

    if args.loop:
        from .loop import run_loop
        latest = snapshots[-1]
        print(f"\n=== Emotional Drift Loop ({args.loop} iterations, backend={args.backend}) ===")
        print(f"Base: {latest}")
        print(latest.as_ctx_table())

        loop_results = run_loop(
            snap=latest,
            iterations=args.loop,
            backend=args.backend,
            verbose=args.verbose,
        )

        for r in loop_results:
            print(r.summary())

        # 最終サマリー
        print(f"\n{'═'*60}")
        print(f"  Loop summary ({args.loop} iterations)")
        print(f"{'─'*60}")
        for r in loop_results:
            if r.error:
                print(f"  iter {r.iteration}: ✗ error")
            else:
                n_conf = len(r.conflicts)
                edges = r.graph_summary
                print(f"  iter {r.iteration}: {edges}  {'⚡ '+str(n_conf)+' conflicts' if n_conf else '✓ stable'}")


if __name__ == "__main__":
    main()
