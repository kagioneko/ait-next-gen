# VN-CPU: Virtual Neural CPU (v0.4)

A lightweight, constrained neural execution runtime that treats ultra-small local LLMs as deterministic instruction cores.

## 🚀 Concept: The "Post-Tape" Computing Era
VN-CPU moves away from free-form chat generation. It enforces a strict **Neural ISA** at the sampler level, ensuring that AI output is always structurally valid, logically consistent, and resource-isolated.

### Paradigms Included:
- **VN-CPU (Neural ISA):** Deterministic 4-character instruction format `[D][T][A][P]`.
- **SEL (Semantic Enzyme Language):** A metabolic 'soup' where enzymes (security/logic) consume threats.
- **CRL (Cognitive Resonance Language):** Vector-based analog logic using 'Chords' and 'Resonators'.

## 🛠️ Architecture

### 1. Neural Core (Isolated Sandbox)
- **Model:** Qwen2.5-0.5B-Instruct (GGUF Q4_K_M).
- **Runtime:** `llama-cpp-python` within a 512MB RAM Docker container.
- **Constraints:**
    - **Sampler Mask:** Forces output into valid ISA token paths.
    - **Logit Bias:** Induces semantic intent based on high-level tasks.
    - **Neural Throttle:** 20ms sleep per token to ensure zero-starvation of host services.

### 2. Runtime & Safety
- **CPL Validator:** Detects logical contradictions in real-time.
- **Rollback Manager:** Automatic state recovery via instruction-level checkpoints.
- **Actuator:** Bridges neural instructions to physical register operations (Memory/Security).

## 📁 Directory Structure
```text
vn_cpu/
├── Dockerfile           # 512MB Sandbox definition
├── docker-compose.yml   # Resource isolation settings
├── isa_builder.py       # Token ID mapping tool
├── core/
│   ├── vn_neural_core_lean.py  # Real GGUF Core with Logit Bias
│   └── vn_sampler_mock.py      # Simulator
└── runtime/
    ├── vn_runtime.py    # Actuator, Registers, and Rollback
    └── ...
```

## ⚡ Quick Start (Inside Sandbox)
```bash
# Build the factory
docker build -t vn_cpu_v04_lean ./vn_cpu

# Launch the Neural Core
docker run -d --name vn_cpu_v04_lean -m 512m --cpus 0.5 -v $(pwd)/vn_cpu:/app/vn-cpu vn_cpu_v04_lean tail -f /dev/null

# Execute a Security Audit & Fix cycle
docker exec vn_cpu_v04_lean python3 /app/vn-cpu/core/vn_neural_core_lean.py
```

---
*Created by Gemini CLI (Antigravity Mode) for the AIT-Next-Gen Project.*
