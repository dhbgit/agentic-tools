#!/usr/bin/env python3
import sys
import os

# Resolve repo root and inject PYTHONPATH
repo_root = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, os.path.join(repo_root, "agentic_tools"))

# Enforce venv execution
venv_python = os.path.expanduser("~/venv/bin/python3")
if os.path.exists(venv_python):
    os.execvp(venv_python, [venv_python, "-m", "orchestrator.run_orchestrator"])
else:
    print("❌ Venv Python not found at ~/venv/bin/python3")
    sys.exit(1)