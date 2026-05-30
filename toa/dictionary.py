"""TOA Dictionary — domain/action/ctx vocabulary"""
from dataclasses import dataclass, field
from typing import Dict


@dataclass
class DomainDef:
    name: str
    desc: str


@dataclass
class ActionDef:
    name: str
    desc: str
    # None = use default LLM handler; callable = native handler
    handler: object = None


@dataclass
class Dictionary:
    domains: Dict[str, DomainDef] = field(default_factory=dict)
    actions: Dict[str, ActionDef] = field(default_factory=dict)
    version: int = 0  # increments on each def: extension (SED-Tape)

    def add_domain(self, char: str, name: str, desc: str = ""):
        self.domains[char] = DomainDef(name, desc)
        self.version += 1

    def add_action(self, char: str, name: str, desc: str = "", handler=None):
        self.actions[char] = ActionDef(name, desc, handler)
        self.version += 1

    def lookup_domain(self, char: str) -> DomainDef:
        if char not in self.domains:
            raise KeyError(f"Unknown domain '{char}' — add it with def:[d:{char}:name]")
        return self.domains[char]

    def lookup_action(self, char: str) -> ActionDef:
        if char not in self.actions:
            raise KeyError(f"Unknown action '{char}' — add it with def:[a:{char}:name]")
        return self.actions[char]


def default_dictionary() -> Dictionary:
    d = Dictionary()
    # domains
    d.domains = {
        's': DomainDef('security',  'Threat detection / hardening'),
        'm': DomainDef('memory',    'Context load/store operations'),
        'n': DomainDef('neural',    'NeuroState / emotion layer'),
        'v': DomainDef('validate',  'Assertion / verification'),
        'a': DomainDef('agent',     'Sub-agent spawn / orchestration'),
        'g': DomainDef('genetic',   'Genetic Shield rule evolution'),
        'c': DomainDef('core',      'OS kernel primitives'),
    }
    # actions
    d.actions = {
        'x': ActionDef('xss',       'Cross-site scripting check'),
        'i': ActionDef('inject',    'SQL / command injection check'),
        'f': ActionDef('fix',       'Apply remediation'),
        'r': ActionDef('read',      'Read / retrieve'),
        'w': ActionDef('write',     'Write / persist'),
        'c': ActionDef('check',     'Generic assertion'),
        'p': ActionDef('prompt',    'Forward to LLM as instruction'),
        'e': ActionDef('emit',      'Emit result to output'),
        'k': ActionDef('kill',      'Terminate / revoke'),
        'z': ActionDef('zero',      'Reset / clear'),
    }
    return d
