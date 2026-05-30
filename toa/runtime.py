"""TOA LLM Runtime

Backends (select via TOA_BACKEND env var):
  claude_cli    — subprocess call to `claude` CLI (default, no key needed)
  codex_cli     — subprocess call to `codex exec` CLI (OpenAI Codex)
  gemini_api    — Google Generative AI SDK (requires GEMINI_API_KEY or Vault OAuth)
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


def _gemini_cli_backend(domain, action, ctx_id, priority, ctx_data):
    # --approval-mode plan: read-only, no tool execution
    # -o text: clean text output, no ANSI / UI decorations
    # system prompt combined into the user prompt (no --system-prompt flag in gemini)
    prompt = f"{_SYSTEM_PROMPT}\n\n{_make_user_msg(domain, action, ctx_id, priority, ctx_data)}"
    try:
        proc = subprocess.run(
            ["gemini", "--approval-mode", "plan", "-o", "text", "-p", prompt],
            capture_output=True, text=True, timeout=60,
        )
        if proc.returncode != 0:
            return None, False, f"[GEMINI-CLI ERROR] {proc.stderr.strip()[:120]}"
        raw = re.sub(r'\x1b\[[0-9;]*m', '', proc.stdout).strip()
        return _parse_response(raw)
    except subprocess.TimeoutExpired:
        return None, False, "[GEMINI-CLI ERROR] timeout"
    except FileNotFoundError:
        return None, False, "[GEMINI-CLI ERROR] `gemini` not found — install @google/gemini-cli"


def _codex_cli_backend(domain, action, ctx_id, priority, ctx_data):
    prompt = f"{_SYSTEM_PROMPT}\n\n{_make_user_msg(domain, action, ctx_id, priority, ctx_data)}"
    try:
        proc = subprocess.run(
            ["codex", "exec", prompt],
            input="",                       # close stdin immediately
            capture_output=True, text=True, timeout=60,
        )
        raw = proc.stdout.strip()
        # Codex prefixes output with a header; grab the last JSON-looking line
        for line in reversed(raw.splitlines()):
            line = line.strip()
            if line.startswith("{") and line.endswith("}"):
                return _parse_response(line)
        # fallback: try the whole output
        return _parse_response(raw)
    except subprocess.TimeoutExpired:
        return None, False, "[CODEX ERROR] timeout"
    except FileNotFoundError:
        return None, False, "[CODEX ERROR] `codex` not found"


def _gemini_api_backend(domain, action, ctx_id, priority, ctx_data):
    # Priority: GEMINI_API_KEY env var → Vault OAuth token
    api_key = os.environ.get("GEMINI_API_KEY")
    access_token = None

    if not api_key:
        try:
            vault_addr  = os.environ.get("VAULT_ADDR",  "https://127.0.0.1:8200")
            vault_cacert = os.environ.get("VAULT_CACERT", "/etc/vault.d/tls/vault-cert.pem")
            proc = subprocess.run(
                ["vault", "kv", "get", "-format=json",
                 "secret/multi-llm-lab/gemini/oauth"],
                capture_output=True, text=True, timeout=10,
                env={**os.environ, "VAULT_ADDR": vault_addr, "VAULT_CACERT": vault_cacert},
            )
            creds = json.loads(json.loads(proc.stdout)["data"]["data"]["credentials"])
            access_token = creds.get("access_token")
        except Exception as e:
            return None, False, f"[GEMINI ERROR] Vault fetch failed: {e}"

    try:
        import google.generativeai as genai
        user_msg = _make_user_msg(domain, action, ctx_id, priority, ctx_data)

        if api_key:
            genai.configure(api_key=api_key)
        else:
            # OAuth bearer token via requests fallback
            import requests
            endpoint = (
                "https://generativelanguage.googleapis.com/v1beta/models/"
                "gemini-2.0-flash:generateContent"
            )
            payload = {
                "system_instruction": {"parts": [{"text": _SYSTEM_PROMPT}]},
                "contents": [{"parts": [{"text": user_msg}]}],
                "generationConfig": {"maxOutputTokens": 256},
            }
            resp = requests.post(
                endpoint,
                headers={"Authorization": f"Bearer {access_token}",
                         "Content-Type": "application/json"},
                json=payload, timeout=30,
            )
            resp.raise_for_status()
            text = resp.json()["candidates"][0]["content"]["parts"][0]["text"]
            return _parse_response(text)

        model = genai.GenerativeModel(
            model_name="gemini-2.0-flash",
            system_instruction=_SYSTEM_PROMPT,
        )
        response = model.generate_content(user_msg)
        return _parse_response(response.text)
    except Exception as e:
        return None, False, f"[GEMINI ERROR] {e}"


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
    "codex_cli":     _codex_cli_backend,
    "gemini_cli":    _gemini_cli_backend,   # Antigravity (gemini -p)
    "gemini_api":    _gemini_api_backend,
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
