import os
import sys

def check_env():
    has_key = bool(os.environ.get('GEMINI_API_KEY'))
    print(f"GEMINI_API_KEY present: {has_key}")
    brain_dir = os.path.expanduser("~/.gemini/antigravity-cli/brain")
    has_brain = os.path.isdir(brain_dir)
    print(f"Brain directory present: {has_brain}")
    if not (has_key and has_brain):
        sys.exit(1)
    print("AWM Environment OK")

if __name__ == '__main__':
    check_env()