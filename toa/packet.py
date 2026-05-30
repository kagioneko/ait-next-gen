"""TOA Packet — parser for the 4-char tape format and special opcodes"""
import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class TOAPacket:
    raw: str
    opcode: str          # 'EXEC' | 'JIF' | 'JMP' | 'CTX_LOAD' | 'CTX_PUSH' | 'DEF'
    domain: Optional[str] = None
    ctx_id: Optional[int] = None
    action: Optional[str] = None
    priority: Optional[int] = None
    operand: Optional[int] = None    # JIF/JMP offset
    def_type: Optional[str] = None  # 'd' or 'a'
    def_char: Optional[str] = None
    def_name: Optional[str] = None

    def __repr__(self):
        if self.opcode == 'EXEC':
            return (f"EXEC  domain={self.domain} ctx=#{self.ctx_id} "
                    f"action={self.action} priority={self.priority}")
        if self.opcode == 'JIF':
            return f"JIF   +{self.operand}"
        if self.opcode == 'JMP':
            return f"JMP   +{self.operand}"
        if self.opcode == 'CTX_LOAD':
            return f"CTX_LOAD  #{self.ctx_id}"
        if self.opcode == 'CTX_PUSH':
            return f"CTX_PUSH  #{self.ctx_id}"
        if self.opcode == 'DEF':
            return f"DEF   [{self.def_type}:{self.def_char}:{self.def_name}]"
        return f"??? {self.raw}"


_HEX = '0123456789abcdef'

def _parse_ctx(ch: str) -> int:
    return _HEX.index(ch.lower())


def parse_packet(token: str) -> TOAPacket:
    token = token.strip()

    # DEF: def:[d:n:neuro] or def:[a:f:fix]
    m = re.fullmatch(r'def:\[([da]):([a-z0-9]):([a-z0-9_\-]+)\]', token)
    if m:
        return TOAPacket(raw=token, opcode='DEF',
                         def_type=m.group(1),
                         def_char=m.group(2),
                         def_name=m.group(3))

    # ?bNN — jump if false (top of stack == 0)
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
    """Split a tape string (newlines / spaces / semicolons as delimiters) into packets."""
    tokens = []
    for line in tape.splitlines():
        line = line.split(';')[0].strip()   # strip inline comments
        if not line:
            continue
        for tok in line.split():
            tokens.append(parse_packet(tok))
    return tokens
