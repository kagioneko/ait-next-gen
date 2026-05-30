"""TOA LLM Runtime

Backends (select via TOA_BACKEND env var):
  claude_cli    — subprocess call to `claude` CLI (default, no key needed)
  anthropic_api — Anthropic SDK (requires ANTHROPIC_API_KEY)
  mock          — offline mock, always succeeds
"""
import json
import os
import re
import subprocess
from typing import Any


# ── system prompt ─────────────────────────────────────────────────────────────

_SYSTEM_PROMPT = (
    "You are a simulation engine for a fictional assembly language called TOA "
    "(Tape-Oriented Assembly). "
    "TOA is an educational / creative coding project that models AI cognition "
    "as a stack machine. Each instruction has: domain, action, ctx (register id), "
    "priority (0-9), and optional data. "
    "When given an instruction, simulate what that operation would logically do "
    "inside the AI cognitive OS, then reply ONLY with this JSON (no markdown, "
    "no code blocks, no extra text): "
    '{"result": <any_value>, "success": true|false, "msg": "<one sentence>"}'
)


# ── helpers ───────────────────────────────────────────────────────────────────

def _strip_fences(text: str) -> str:
    """Remove ```json ... ``` or ``` ... ``` wrappers if present."""
    text = text.strip()
    m = re.match(r'^```(?:json)?\s*([\s\S]+?)\s*```$', text)
    return m.group(1) if m else text


def _parse_response(raw: str) -> tuple[Any, bool, str]:
    raw = _strip_fences(raw)
    try:
        parsed = json.loads(raw)
        return (
            parsed.get("result", raw),
            bool(parsed.get("success", True)),
            parsed.get("msg", ""),
        )
    except json.JSONDecodeError:
        # non-JSON reply — treat as a plain string result
        return raw, True, "[raw text response]"


def _make_user_msg(domain, action, ctx_id, priority, ctx_data) -> str:
    return (
        f"domain={domain} action={action} "
        f"ctx=#{ctx_id} priority={priority} "
        f"data={repr(ctx_data)[:200]}"
    )


# ── backends ──────────────────────────────────────────────────────────────────

def _mock_backend(domain, action, ctx_id, priority, ctx_data):
    return (
        f"MOCK:{domain}.{action}",
        True,
        f"[MOCK] domain={domain} action={action} ctx=#{ctx_id} p={priority}",
    )


def _claude_cli_backend(domain, action, ctx_id, priority, ctx_data):
    user_msg = _make_user_msg(domain, action, ctx_id, priority, ctx_data)
    try:
        proc = subprocess.run(
            ["claude", "--system-prompt", _SYSTEM_PROMPT, "-p", user_msg],
            capture_output=True, text=True, timeout=30,
        )
        if proc.returncode != 0:
            return None, False, f"[CLI ERROR] {proc.stderr.strip()[:120]}"
        return _parse_response(proc.stdout)
    except subprocess.TimeoutExpired:
        return None, False, "[CLI ERROR] timeout"
    except FileNotFoundError:
        return None, False, "[CLI ERROR] `claude` not found — is Claude Code installed?"


def _anthropic_api_backend(domain, action, ctx_id, priority, ctx_data):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return None, False, "[API ERROR] ANTHROPIC_API_KEY not set"
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=256,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _make_user_msg(domain, action, ctx_id, priority, ctx_data)}],
        )
        return _parse_response(response.content[0].text)
    except Exception as e:
        return None, False, f"[API ERROR] {e}"


# ── selector ──────────────────────────────────────────────────────────────────

_BACKENDS = {
    "claude_cli":    _claude_cli_backend,
    "anthropic_api": _anthropic_api_backend,
    "mock":          _mock_backend,
}


def get_backend():
    """Return the backend function selected by TOA_BACKEND env var (default: claude_cli)."""
    name = os.environ.get("TOA_BACKEND", "claude_cli")
    if name not in _BACKENDS:
        raise ValueError(f"Unknown TOA_BACKEND '{name}'. Choose from: {list(_BACKENDS)}")
    return _BACKENDS[name]


# default export used by machine.py
def llm_backend(domain, action, ctx_id, priority, ctx_data):
    return get_backend()(domain, action, ctx_id, priority, ctx_data)
