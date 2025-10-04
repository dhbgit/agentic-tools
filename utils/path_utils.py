# agentic_tools/utils/path_utils.py
import os

def get_repo_root():
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))