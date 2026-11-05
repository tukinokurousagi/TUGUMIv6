import sys
import os
import subprocess

def main():
    query = sys.argv[1] if len(sys.argv) > 1 else '本日の全体運'
    base_script = os.path.expanduser('~/.agents/skills/senji-ryakketsu-rokujin/scripts/senji_advisor.py')
    if os.path.exists(base_script):
        cmd = ['python3', base_script, query]
    else:
        cmd = ['echo', f'[擬似鑑定] 問い合わせ「{query}」に対する六壬鑑定を実行しました。']
    res = subprocess.run(cmd, capture_output=True, text=True)
    print(res.stdout)
    if res.stderr:
        print(res.stderr, file=sys.stderr)
    sys.exit(res.returncode)

if __name__ == '__main__':
    main()
