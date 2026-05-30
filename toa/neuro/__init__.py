"""toa.neuro — NeuroState × TOA integration

Maps しーちゃん's emotion snapshots from spirit.db to TOA #ctx registers,
runs CPL conflict analysis, and generates emotion-driven TOA tapes via LLM.

Usage:
    python -m toa.neuro               # 最新5スナップショットをシミュレート
    python -m toa.neuro --history 10  # 直近10件
    python -m toa.neuro --generate    # LLMテープ自己生成も実行
    python -m toa.neuro --verbose     # TOA実行ログ詳細表示
"""
from .loader import load_snapshots, load_latest, NeuroSnapshot
from .mapper import CTX_TO_DIM, DIM_TO_CTX, CPL_RULES, build_neuro_dictionary
from .simulator import run_simulation, SimResult

__all__ = [
    "NeuroSnapshot",
    "load_snapshots",
    "load_latest",
    "CTX_TO_DIM",
    "DIM_TO_CTX",
    "CPL_RULES",
    "build_neuro_dictionary",
    "run_simulation",
    "SimResult",
]
