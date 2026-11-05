import glob
import os
import sys

def purge_files(pattern):
    targets = glob.glob(pattern)
    print(f"Found {len(targets)} files matching: {pattern}")
    for f in targets:
        try:
            os.remove(f)
        except OSError as e:
            print(f"Error deleting {f}: {e}", file=sys.stderr)
    remaining = glob.glob(pattern)
    print(f"Remaining: {len(remaining)}")
    return len(remaining) == 0

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python safe_purge.py '<glob_pattern>'")
        sys.exit(1)
    success = purge_files(sys.argv[1])
    sys.exit(0 if success else 1)
