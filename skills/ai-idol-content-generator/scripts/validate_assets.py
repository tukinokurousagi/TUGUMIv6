import os, sys

def check_assets(target_dir):
    if not os.path.isdir(target_dir):
        print(f"Error: Directory not found: {target_dir}")
        sys.exit(1)
    files = os.listdir(target_dir)
    print(f"Found {len(files)} files in {target_dir}")
    for f in files:
        path = os.path.join(target_dir, f)
        print(f" - {f}: {os.path.getsize(path)} bytes")

if __name__ == '__main__':
    if len(sys.argv) > 1:
        check_assets(sys.argv[1])
    else:
        print("Usage: python validate_assets.py <directory>")