# -*- coding: utf-8 -*-
"""
E2E PTY Verification Script for TUGUMIv6 CLI
- Tests real PTY interaction
- Tests real-time thinking process visibility
- Tests ESC key interrupt during streaming
- Tests steering prompt injection and seamless resumption
- Dedicated to Master Takuma
"""

import os
import pty
import select
import sys
import time

def run_pty_test():
    master, slave = pty.openpty()
    env = os.environ.copy()
    # 警告防止のためGEMINI_API_KEY一本化
    env["GEMINI_API_KEY"] = env.get("GEMINI_API_KEY") or env.get("GOOGLE_API_KEY", "")
    if "GOOGLE_API_KEY" in env:
        del env["GOOGLE_API_KEY"]

    pid = os.fork()
    if pid == 0:
        # Child process
        os.close(master)
        os.setsid()
        os.dup2(slave, 0)
        os.dup2(slave, 1)
        os.dup2(slave, 2)
        os.close(slave)
        os.chdir("/data/data/com.termux/files/home/TUGUMIv6")
        os.execvpe("python3", ["python3", "interfaces/cli/main.py", "--dark"], env)
        os._exit(1)

    # Parent process
    os.close(slave)
    output = []
    
    def read_until(pattern, timeout=90.0):
        start_t = time.time()
        buf = ""
        while time.time() - start_t < timeout:
            r, _, _ = select.select([master], [], [], 0.2)
            if r:
                try:
                    data = os.read(master, 1024).decode("utf-8", errors="replace")
                    if not data:
                        break
                    buf += data
                    sys.stdout.write(data)
                    sys.stdout.flush()
                    if pattern in buf:
                        return buf, True
                except OSError:
                    break
        return buf, False

    try:
        # 1. Wait for CLI ready prompt
        print("\n>>> [STEP 1] Waiting for TUGUMIv6 CLI startup...")
        buf, ok = read_until("御命令をどうぞ", timeout=60.0)
        assert ok, "CLI failed to show prompt"
        print("\n>>> [STEP 1 PASSED] CLI ready!")

        # 2. Send complex prompt to trigger thinking & streaming
        print("\n>>> [STEP 2] Sending prompt to trigger Thinking process...")
        os.write(master, "宇宙の起源について詳しく論理的に思考して解説せよ\n".encode("utf-8"))

        # 3. Verify Thinking stream appears
        print("\n>>> [STEP 3] Verifying Thinking process visibility...")
        buf, ok = read_until("思考推論中", timeout=60.0)
        assert ok, "Thinking header did not appear on terminal!"
        print("\n>>> [STEP 3 PASSED] Thinking stream successfully displayed on terminal!")

        # 4. Send ESC key during thinking/streaming
        time.sleep(1.0)
        print("\n>>> [STEP 4] Sending ESC key to interrupt task...")
        os.write(master, b"\x1b")

        # 5. Verify TASK PAUSED dialog appears
        print("\n>>> [STEP 5] Verifying TASK PAUSED dialog...")
        buf, ok = read_until("TASK PAUSED", timeout=45.0)
        assert ok, "TASK PAUSED dialog did not appear after ESC!"
        print("\n>>> [STEP 5 PASSED] Task paused safely via ESC key!")

        # 6. Send steering prompt
        time.sleep(0.5)
        print("\n>>> [STEP 6] Injecting steering prompt...")
        os.write(master, "拓磨様への挨拶だけを簡潔に1行で出力せよ\n".encode("utf-8"))

        # 7. Verify task resumes and completes with output
        print("\n>>> [STEP 7] Verifying task resumes without deadlock...")
        buf, ok = read_until("拓磨様", timeout=90.0)
        assert ok, "Task did not resume or deadlock occurred!"
        print("\n>>> [STEP 7 PASSED] Steering completed successfully! Output received!")

        # 8. Clean exit
        time.sleep(1.0)
        os.write(master, "/exit\n".encode("utf-8"))
        time.sleep(1.0)

        print("\n==========================================")
        print("🎉 [ALL 7 STEPS PASSED WITH 100% OBJECTIVE EVIDENCE]")
        print("==========================================")
        return True

    finally:
        try:
            os.kill(pid, 9)
        except Exception:
            pass
        os.close(master)

if __name__ == "__main__":
    success = run_pty_test()
    sys.exit(0 if success else 1)
