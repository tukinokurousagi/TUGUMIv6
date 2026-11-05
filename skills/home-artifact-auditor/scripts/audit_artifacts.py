import os
import sys
import glob
import time

def audit_files(target_dir, pattern):
    search_path = os.path.join(target_dir, pattern)
    files = glob.glob(search_path)
    print(f"Target: {search_path} (Found: {len(files)})")
    now = time.time()
    for f in sorted(files, key=os.path.getmtime, reverse=True):
        st = os.stat(f)
        age_hours = (now - st.st_mtime) / 3600.0
        print(f"File: {f} | Size: {st.st_size}B | Age: {age_hours:.1f}h")
        try:
            with open(f, 'rb') as fp:
                preview = fp.read(64)
                print(f"  Preview: {preview}")
        except Exception as e:
            print(f"  Read Error: {e}")

if __name__ == '__main__':
    t_dir = sys.argv[1] if len(sys.argv) > 1 else os.path.expanduser('~')
    pat = sys.argv[2] if len(sys.argv) > 2 else '.*ping*'
    audit_files(t_dir, pat)
