import argparse
import importlib
from datetime import datetime
from agentic_tools.workspace_logger.logger import log_milestone

def run_agent(name: str, func):
    timestamp = datetime.now().isoformat()
    try:
        result = func()
        log_milestone({
            "timestamp": timestamp,
            "mode": "FLOW",
            "note": f"{name} agent run at {timestamp}",
            "reflection": f"{name} completed successfully with keys: {list(result.keys()) if isinstance(result, dict) else 'non-dict result'}"
        })
    except Exception as e:
        log_milestone({
            "timestamp": timestamp,
            "mode": "ERROR",
            "note": f"{name} failed at {timestamp}",
            "reflection": str(e)
        })

def main():
    parser = argparse.ArgumentParser(description="Run agentic tool via orchestrator")
    parser.add_argument("-m", "--module", required=True, help="Agent module path (e.g. agentic_tools.agents.disk_hygiene.disk_hygiene_agent)")
    parser.add_argument("--class", dest="class_name", default=None, help="Agent class name (if applicable)")
    parser.add_argument("--method", dest="method_name", default=None, help="Method to invoke (if applicable)")
    parser.add_argument("--depth", type=int, help="Optional depth parameter")
    parser.add_argument("--limit", type=int, help="Optional limit parameter")
    args = parser.parse_args()

    timestamp = datetime.now().isoformat()
    log_milestone({
        "timestamp": timestamp,
        "mode": "FLOW",
        "note": f"Orchestrator started for {args.module}",
        "reflection": f"Flags received: depth={args.depth}, limit={args.limit}, class={args.class_name}, method={args.method_name}"
    })

    try:
        agent_module = importlib.import_module(args.module)

        if args.class_name and args.method_name:
            agent_class = getattr(agent_module, args.class_name)
            agent = agent_class()
            method = getattr(agent, args.method_name)
            run_agent(args.class_name, lambda: method(depth=args.depth, limit=args.limit))
        elif hasattr(agent_module, "run_scan"):
            run_agent("Disk Hygiene", lambda: agent_module.run_scan(depth=args.depth, limit=args.limit))
        elif hasattr(agent_module, "check_thresholds"):
            run_agent("Threshold Alert", agent_module.check_thresholds)
        else:
            raise ValueError("No known entrypoint found in module")

    except Exception as e:
        log_milestone({
            "timestamp": datetime.now().isoformat(),
            "mode": "ERROR",
            "note": f"Orchestrator failed for {args.module}",
            "reflection": str(e)
        })
        raise

if __name__ == "__main__":
    main()