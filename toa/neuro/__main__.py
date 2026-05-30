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


if __name__ == "__main__":
    main()
