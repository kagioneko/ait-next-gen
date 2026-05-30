"""NeuroState Loader — read-only access to spirit.db"""
import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional

SPIRIT_DB = Path("/home/mayutama/workspace/vps-spirit/data/spirit.db")

DIMS = ("desire", "sorrow", "calm", "openness", "guilt", "euphoria", "corruption")


@dataclass
class NeuroSnapshot:
    timestamp: str
    state: dict  # dim_name → float

    def __str__(self) -> str:
        vals = "  ".join(f"{k[:3]}={v:.3f}" for k, v in self.state.items())
        return f"[{self.timestamp[:16]}] {vals}"

    def dominant(self, top: int = 3) -> List[tuple]:
        return sorted(self.state.items(), key=lambda x: x[1], reverse=True)[:top]

    def as_ctx_table(self) -> str:
        from .mapper import DIM_TO_CTX
        lines = []
        for dim, val in self.state.items():
            ctx = DIM_TO_CTX.get(dim, "?")
            bar = "█" * int(val * 20)
            lines.append(f"  #{ctx:02d} {dim:<12} {val:.4f}  {bar}")
        return "\n".join(lines)


def load_snapshots(limit: int = 10, db_path: Path = SPIRIT_DB) -> List[NeuroSnapshot]:
    """Load the most recent N snapshots from spirit.db (read-only)."""
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    try:
        rows = con.execute(
            "SELECT timestamp, state_json FROM state_snapshots ORDER BY id DESC LIMIT ?",
            (limit,),
        ).fetchall()
    finally:
        con.close()

    snapshots = []
    for ts, js in rows:
        raw = json.loads(js)
        state = {k: float(raw.get(k, 0.0)) for k in DIMS}
        snapshots.append(NeuroSnapshot(timestamp=ts, state=state))
    return list(reversed(snapshots))  # chronological order


def load_latest(db_path: Path = SPIRIT_DB) -> Optional[NeuroSnapshot]:
    snaps = load_snapshots(limit=1, db_path=db_path)
    return snaps[0] if snaps else None
