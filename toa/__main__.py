"""TOA REPL — run with: python -m toa"""
import sys
from .machine import TOAMachine
from .runtime import llm_backend
from .packet import parse_packet


BANNER = """
╔══════════════════════════════════════════════════╗
║  TOA v0.2  ·  Tape-Oriented Assembly for LLMs   ║
║  type 'help' for commands, 'quit' to exit        ║
╚══════════════════════════════════════════════════╝
"""

HELP = """
Commands:
  run <tape>     Execute a single-line tape (space-separated packets)
  file <path>    Execute a tape file
  ctx            Show all ctx registers
  stack          Show current stack
  graph          Show CPL graph (edges + conflicts)
  dict           Show active dictionary
  help           This message
  quit           Exit

Packet syntax:
  s4x9           EXEC  domain=s ctx=#4 action=x priority=9
  ?b03           JIF   skip 3 packets if stack top == 0
  !005           JMP   unconditional jump +5
  ##04           CTX_LOAD  make #4 the active context
  >>02           CTX_PUSH  pop stack → #2
  def:[d:n:neuro]  DEF   add domain 'n' = 'neuro'
  def:[a:f:fix]    DEF   add action 'f' = 'fix'

CPL link syntax (whole line):
  #01 =>creates=> #02     link: #1 creates #2
  #02 ==requires=> #03    link: #2 requires #3
  #02 ==violates=> #04    link: #2 violates #4  (triggers conflict if also requires)
"""


def main():
    print(BANNER)
    machine = TOAMachine(backend=llm_backend, verbose=True)
    state = None

    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue

        if line in ('quit', 'exit', 'q'):
            break

        if line == 'help':
            print(HELP)
            continue

        if line == 'ctx':
            if state:
                for k, v in state.ctx.items():
                    print(f"  #{k:02d} = {repr(v)[:60]}")
            else:
                print("  (no state yet)")
            continue

        if line == 'stack':
            if state:
                print(f"  {state.stack}")
            else:
                print("  (no state yet)")
            continue

        if line == 'graph':
            if state:
                print(state.graph.render())
                print(state.graph.summary())
            else:
                print("  (no state yet)")
            continue

        if line == 'dict':
            d = machine.dict
            print(f"  Dictionary v{d.version}")
            print("  Domains:", {k: v.name for k, v in d.domains.items()})
            print("  Actions:", {k: v.name for k, v in d.actions.items()})
            continue

        if line.startswith('file '):
            path = line[5:].strip()
            try:
                tape = open(path).read()
                state = machine.run(tape)
                print(f"\n[DONE] ip={state.ip}  stack={state.stack}")
            except Exception as e:
                print(f"[ERROR] {e}")
            continue

        if line.startswith('run '):
            tape = line[4:]
        else:
            tape = line

        try:
            state = machine.run(tape)
            print(f"\n[DONE] ip={state.ip}  stack={state.stack}")
        except Exception as e:
            print(f"[ERROR] {e}")

    print("[TOA] exit")


if __name__ == '__main__':
    main()
