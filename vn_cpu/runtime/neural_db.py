"""Neural DB Logger for UNO

Handles persistent storage of organism heartbeats, metabolic reactions,
acoustic resonance, and register states using SQLite.
"""
import sqlite3
import json
import logging
from datetime import datetime
from typing import Dict, Any, List

logger = logging.getLogger("uno.db")

class NeuralDB:
    def __init__(self, db_path: str = "/app/vn_cpu/uno_spirit.db"):
        self.db_path = db_path
        self._init_db()

    def _init_db(self):
        """Initializes the database schema."""
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            # 1. Pulses (Instructions)
            c.execute('''CREATE TABLE IF NOT EXISTS pulses
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          timestamp DATETIME,
                          instruction TEXT,
                          action_msg TEXT)''')
            
            # 2. Metabolism (Enzymes)
            c.execute('''CREATE TABLE IF NOT EXISTS metabolism
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          timestamp DATETIME,
                          enzyme_name TEXT,
                          result TEXT)''')
            
            # 3. Resonance (Acoustics)
            c.execute('''CREATE TABLE IF NOT EXISTS resonance
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          timestamp DATETIME,
                          resonator_name TEXT,
                          similarity REAL)''')
            
            # 4. Snapshots (Register States)
            c.execute('''CREATE TABLE IF NOT EXISTS snapshots
                         (id INTEGER PRIMARY KEY AUTOINCREMENT,
                          timestamp DATETIME,
                          register_data TEXT)''') # JSON blob
            conn.commit()
        logger.info(f"Neural DB initialized at {self.db_path}")

    def log_pulse(self, instruction: str, msg: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO pulses (timestamp, instruction, action_msg) VALUES (?, ?, ?)",
                         (datetime.now(), instruction, msg))

    def log_metabolism(self, enzyme: str, result: str):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO metabolism (timestamp, enzyme_name, result) VALUES (?, ?, ?)",
                         (datetime.now(), enzyme, result))

    def log_resonance(self, name: str, sim: float):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO resonance (timestamp, resonator_name, similarity) VALUES (?, ?, ?)",
                         (datetime.now(), name, sim))

    def save_snapshot(self, ctx: Dict[str, Any]):
        # Only save non-empty registers to save space
        clean_ctx = {k: str(v) for k, v in ctx.items() if v and "Empty" not in str(v)}
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("INSERT INTO snapshots (timestamp, register_data) VALUES (?, ?)",
                         (datetime.now(), json.dumps(clean_ctx)))

    def prune(self, days: int = 7):
        """Removes records older than 'days' to prevent bloat."""
        logger.info(f"Pruning Neural DB records older than {days} days...")
        with sqlite3.connect(self.db_path) as conn:
            c = conn.cursor()
            limit_date = datetime.now()
            # Simple SQL to delete old records
            # Note: timestamp in SQLite depends on how it was inserted. 
            # Here we inserted datetime.now() which is usually a string.
            for table in ["pulses", "metabolism", "resonance", "snapshots"]:
                c.execute(f"DELETE FROM {table} WHERE timestamp < date('now', '-{days} days')")
            conn.commit()
            c.execute("VACUUM")
            conn.commit()
        logger.info("✅ Neural DB pruning complete.")
