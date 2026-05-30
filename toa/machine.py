"""TOA Stack Machine — LLM-agnostic core execution engine"""
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

from .dictionary import Dictionary, default_dictionary
from .packet import TOAPacket, tokenize


# ── result types ────────────────────────────────────────────────────────────

@dataclass
class ExecResult:
    packet: TOAPacket
    value: Any
    success: bool
    msg: str = ""


# ── machine state ────────────────────────────────────────────────────────────

@dataclass
class TOAMachineState:
    stack: List[Any] = field(default_factory=list)
    ctx: Dict[int, Any] = field(default_factory=dict)   # #0 .. #15
    active_ctx: int = 0
    ip: int = 0
    halted: bool = False
    trace: List[str] = field(default_factory=list)

    def push(self, v): self.stack.append(v)
    def pop(self) -> Any: return self.stack.pop() if self.stack else None
    def peek(self) -> Any: return self.stack[-1] if self.stack else None


# ── handler type ─────────────────────────────────────────────────────────────

# A backend is a callable:
#   (domain: str, action: str, ctx_id: int, priority: int, ctx_data: Any) -> (value: Any, success: bool, msg: str)
Backend = Callable[[str, str, int, int, Any], tuple[Any, bool, str]]


def mock_backend(domain: str, action: str, ctx_id: int, priority: int, ctx_data: Any):
    """Default mock backend — used for offline testing."""
    msg = (f"[MOCK] domain={domain} action={action} "
           f"ctx=#{ctx_id} priority={priority} data={repr(ctx_data)[:40]}")
    return f"OK:{domain}{action}", True, msg


# ── machine ──────────────────────────────────────────────────────────────────

class TOAMachine:
    def __init__(
        self,
        dictionary: Optional[Dictionary] = None,
        backend: Optional[Backend] = None,
        verbose: bool = True,
    ):
        self.dict = dictionary or default_dictionary()
        self.backend = backend or mock_backend
        self.verbose = verbose

    # ── public API ────────────────────────────────────────────────────────

    def run(self, tape: str) -> TOAMachineState:
        packets = tokenize(tape)
        state = TOAMachineState()
        return self._execute(packets, state)

    def run_packets(self, packets: list[TOAPacket]) -> TOAMachineState:
        state = TOAMachineState()
        return self._execute(packets, state)

    # ── internal execution loop ───────────────────────────────────────────

    def _execute(self, packets: List[TOAPacket], state: TOAMachineState) -> TOAMachineState:
        while state.ip < len(packets) and not state.halted:
            pkt = packets[state.ip]
            self._log(state, f"[IP:{state.ip:03d}] {pkt}")
            self._dispatch(pkt, state)
            state.ip += 1
        return state

    def _dispatch(self, pkt: TOAPacket, state: TOAMachineState):
        match pkt.opcode:
            case 'EXEC':
                self._exec(pkt, state)
            case 'JIF':
                top = state.peek()
                if not top:
                    state.ip += pkt.operand
                    self._log(state, f"  → JIF taken (+{pkt.operand})")
            case 'JMP':
                state.ip += pkt.operand
                self._log(state, f"  → JMP +{pkt.operand}")
            case 'CTX_LOAD':
                state.active_ctx = pkt.ctx_id
                self._log(state, f"  → active ctx → #{pkt.ctx_id}")
            case 'CTX_PUSH':
                val = state.pop()
                state.ctx[pkt.ctx_id] = val
                self._log(state, f"  → #{pkt.ctx_id} ← {repr(val)[:40]}")
            case 'DEF':
                self._def(pkt)
            case _:
                self._log(state, f"  !! unknown opcode {pkt.opcode}")

    def _exec(self, pkt: TOAPacket, state: TOAMachineState):
        # validate dict
        try:
            dom = self.dict.lookup_domain(pkt.domain)
            act = self.dict.lookup_action(pkt.action)
        except KeyError as e:
            state.push(0)
            self._log(state, f"  !! {e}")
            return

        ctx_data = state.ctx.get(pkt.ctx_id)

        # native handler takes priority
        if act.handler is not None:
            value, ok, msg = act.handler(pkt.domain, pkt.action, pkt.ctx_id, pkt.priority, ctx_data)
        else:
            value, ok, msg = self.backend(dom.name, act.name, pkt.ctx_id, pkt.priority, ctx_data)

        self._log(state, f"  → {msg}")
        state.push(1 if ok else 0)
        state.ctx[pkt.ctx_id] = value   # write result back to same ctx slot

    def _def(self, pkt: TOAPacket):
        if pkt.def_type == 'd':
            self.dict.add_domain(pkt.def_char, pkt.def_name,
                                  f"[Dynamic] added at dict v{self.dict.version}")
        else:
            self.dict.add_action(pkt.def_char, pkt.def_name,
                                  f"[Dynamic] added at dict v{self.dict.version}")
        self._log(None, f"  DEF dict[{pkt.def_type}:{pkt.def_char}] = '{pkt.def_name}'  "
                        f"(dict v{self.dict.version})")

    def _log(self, state, msg: str):
        if self.verbose:
            print(msg)
        if state is not None:
            state.trace.append(msg)
