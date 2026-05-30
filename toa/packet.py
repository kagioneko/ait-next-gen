"""TOA Packet — parser for the 4-char tape format, special opcodes, and CPL links"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class TOAPacket:
    raw: str
    opcode: str
    # EXEC fields
    domain: Optional[str] = None
    ctx_id: Optional[int] = None
    action: Optional[str] = None
    priority: Optional[int] = None
    # JIF / JMP
    operand: Optional[int] = None
    # DEF
    def_type: Optional[str] = None
    def_char: Optional[str] = None
    def_name: Optional[str] = None
    # CPL_LINK
    cpl_src: Optional[int] = None
    cpl_edge: Optional[str] = None
    cpl_dst: Optional[int] = None

    def __repr__(self):
        match self.opcode:
            case 'EXEC':
                return (f"EXEC  domain={self.domain} ctx=#{self.ctx_id} "
                        f"action={self.action} priority={self.priority}")
            case 'JIF':
                return f"JIF   +{self.operand}"
            case 'JMP':
                return f"JMP   +{self.operand}"
            case 'CTX_LOAD':
                return f"CTX_LOAD  #{self.ctx_id}"
            case 'CTX_PUSH':
                return f"CTX_PUSH  #{self.ctx_id}"
            case 'DEF':
                return f"DEF   [{self.def_type}:{self.def_char}:{self.def_name}]"
            case 'CPL_LINK':
                return f"LINK  #{self.cpl_src:02d} =={self.cpl_edge}==> #{self.cpl_dst:02d}"
            case _:
                return f"??? {self.raw}"


_HEX = '0123456789abcdef'

def _parse_ctx(ch: str) -> int:
    return _HEX.index(ch.lower())


# CPL link: #04 =>creates=> #09  or  #4 ==violates=> #9
_CPL_RE = re.compile(
    r'^#([0-9a-f]{1,2})\s*(?:=>|==)([a-z]+)=>\s*#([0-9a-f]{1,2})$',
    re.IGNORECASE,
)


def parse_line(line: str) -> Optional[TOAPacket]:
    """Try to parse a whole line as a CPL link. Returns None if it doesn't match."""
    m = _CPL_RE.fullmatch(line.strip())
    if m:
        return TOAPacket(
            raw=line.strip(), opcode='CPL_LINK',
            cpl_src=int(m.group(1), 16),
            cpl_edge=m.group(2).lower(),
            cpl_dst=int(m.group(3), 16),
        )
    return None


def parse_packet(token: str) -> TOAPacket:
    token = token.strip()

    # DEF: def:[d:n:neuro] or def:[a:f:fix]
    m = re.fullmatch(r'def:\[([da]):([a-z0-9]):([a-z0-9_\-]+)\]', token)
    if m:
        return TOAPacket(raw=token, opcode='DEF',
                         def_type=m.group(1),
                         def_char=m.group(2),
                         def_name=m.group(3))

    # ?bNN — jump if false
    m = re.fullmatch(r'\?b([0-9a-f]{2})', token)
    if m:
        return TOAPacket(raw=token, opcode='JIF', operand=int(m.group(1), 16))

    # !NNN — unconditional jump
    m = re.fullmatch(r'!([0-9a-f]{3})', token)
    if m:
        return TOAPacket(raw=token, opcode='JMP', operand=int(m.group(1), 16))

    # ##NN — load ctx into active register
    m = re.fullmatch(r'##([0-9a-f]{2})', token)
    if m:
        return TOAPacket(raw=token, opcode='CTX_LOAD', ctx_id=int(m.group(1), 16))

    # >>NN — push stack top into ctx
    m = re.fullmatch(r'>>([0-9a-f]{2})', token)
    if m:
        return TOAPacket(raw=token, opcode='CTX_PUSH', ctx_id=int(m.group(1), 16))

    # EXEC: [domain][ctx_hex][action][priority]
    if len(token) == 4:
        domain, ctx_ch, action, prio_ch = token
        if ctx_ch in _HEX and prio_ch.isdigit():
            return TOAPacket(
                raw=token, opcode='EXEC',
                domain=domain,
                ctx_id=_parse_ctx(ctx_ch),
                action=action,
                priority=int(prio_ch),
            )

    raise ValueError(f"Cannot parse TOA token: '{token}'")


def tokenize(tape: str) -> list[TOAPacket]:
    """Parse a tape string into packets.

    Lines matching the CPL link syntax (#src =>type=> #dst) are parsed as a
    single CPL_LINK packet. All other lines are split by whitespace and each
    token parsed as a standard TOA packet.
    """
    tokens = []
    for line in tape.splitlines():
        line = line.split(';')[0].strip()
        if not line:
            continue
        # Try whole-line CPL link first
        cpl = parse_line(line)
        if cpl:
            tokens.append(cpl)
            continue
        # Otherwise tokenize normally
        for tok in line.split():
            tokens.append(parse_packet(tok))
    return tokens
