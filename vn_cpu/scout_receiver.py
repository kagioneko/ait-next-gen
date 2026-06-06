import json
import logging
import os
from pathlib import Path

logger = logging.getLogger("vn-cpu.receiver")
TAPE_FILE = "/app/shii-chan-mcp/data/tapes.json"
INBOX_FILE = "/app/shii-chan-mcp/data/scout_inbox.json"

def sync_inbox():
    if not os.path.exists(INBOX_FILE):
        return

    try:
        with open(INBOX_FILE, "r") as f:
            new_tapes = json.load(f)
        
        if not os.path.exists(TAPE_FILE):
            existing_tapes = {}
        else:
            with open(TAPE_FILE, "r") as f:
                existing_tapes = json.load(f)
        
        # Merge
        count = 0
        for tid, tval in new_tapes.items():
            if tid not in existing_tapes:
                existing_tapes[tid] = tval
                count += 1
        
        with open(TAPE_FILE, "w") as f:
            json.dump(existing_tapes, f, indent=2)
            
        os.remove(INBOX_FILE)
        logger.info(f"✅ Sync complete: Ingested {count} tapes from external scout.")
    except Exception as e:
        logger.error(f"Sync failed: {e}")

if __name__ == "__main__":
    sync_inbox()
