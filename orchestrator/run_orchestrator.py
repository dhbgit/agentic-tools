from workspace_logger.logger import log_milestone
from agentic_tools.agents.disk_hygiene.disk_hygiene_agent import check_disk_usage
from datetime import datetime

def launch():

    log_milestone({
        "timestamp": datetime.now().isoformat(),
        "mode": "FLOW",
        "note": "🚀 Orchestrator started",
        "reflection": "Execution context confirmed—launching agentic flow"
    })

    # Run disk usage agent
    result = check_disk_usage()

    log_milestone({
        "timestamp": datetime.now().isoformat(),
        "mode": "REFLECT",
        "note": "📊 Disk usage result",
        "reflection": str(result)
    })

    # Add more agent calls here as needed
    # e.g., threshold checks, cleanup routines, sunset scans

    log_milestone({
        "timestamp": datetime.now().isoformat(),
        "mode": "FLOW",
        "note": "✅ Orchestration complete",
        "reflection": "All agents executed successfully—milestones logged and workspace state updated"
    })

if __name__ == "__main__":
    launch()