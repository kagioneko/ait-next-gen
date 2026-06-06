import sys
import os
sys.path.append("/app")
sys.path.append("/app/vn_cpu")
sys.path.append("/app/shii-chan-mcp")
from organism import UnifiedOrganism

print("--- Manually Triggering Shii-chan's Journaling ---")
org = UnifiedOrganism(mode="all")
journal = org.reflector.generate_daily_journal()
print(f"\nResulting Journal:\n{journal}")
