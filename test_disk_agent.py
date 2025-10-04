from agents.disk_hygiene.disk_hygiene_agent import DiskHygieneAgent
from workspace_logger.logger import log_milestone
from datetime import datetime

# Run the agent
agent = DiskHygieneAgent()
result = agent.scan()

# Load manual du output
with open("manual_du.txt") as f:
    manual_lines = f.readlines()

# Normalize manual paths
manual_paths = set(line.strip().split()[-1] for line in manual_lines)

# Normalize agent paths (parsed as dicts)
agent_paths = set(entry["path"] for entry in result["du"][:10])

# Compare top 10 agent paths to manual snapshot
matches = agent_paths.issubset(manual_paths)

# Log result
log_milestone({
    "timestamp": datetime.now().isoformat(),
    "mode": "VALIDATE",
    "note": "Agent du output matches manual snapshot" if matches else "Mismatch between agent and manual du output",
    "reflection": "Confirmed fidelity of disk hygiene agent" if matches else "Agent needs refinement or deeper parsing"
})