import argparse
import glob
import json
import os
import sys

def find_latest_transcript(brain_dir, session_id=None):
    base = os.path.expanduser(brain_dir)
    if not os.path.exists(base):
        return None
    if session_id:
        target_dir = os.path.join(base, session_id)
    else:
        dirs = [os.path.join(base, d) for d in os.listdir(base) if os.path.isdir(os.path.join(base, d))]
        if not dirs:
            return None
        target_dir = max(dirs, key=os.path.getmtime)
    
    full_p = os.path.join(target_dir, ".system_generated", "logs", "transcript_full.jsonl")
    short_p = os.path.join(target_dir, ".system_generated", "logs", "transcript.jsonl")
    if os.path.exists(full_p):
        return full_p
    if os.path.exists(short_p):
        return short_p
    return None

def parse_nested_result(content_str):
    if "```json\n" in content_str:
        try:
            block = content_str.split("```json\n")[1].split("\n```")[0]
            outer = json.loads(block)
            if "result" in outer and isinstance(outer["result"], str):
                inner = json.loads(outer["result"])
                return f"STDOUT:\n{inner.get('stdout', '')}\nSTDERR:\n{inner.get('stderr', '')}"
            return json.dumps(outer, ensure_ascii=False, indent=2)
        except Exception:
            pass
    return content_str

def main():
    parser = argparse.ArgumentParser(description="Recover context from recent session transcript.")
    parser.add_argument("--brain-dir", default="~/.gemini/antigravity/brain")
    parser.add_argument("--session-id", default=None)
    parser.add_argument("--lines", type=int, default=10)
    parser.add_argument("--step", type=int, default=None)
    args = parser.parse_args()

    path = find_latest_transcript(args.brain_dir, args.session_id)
    if not path:
        print("Transcript file not found.", file=sys.stderr)
        sys.exit(1)

    print(f"Reading transcript: {path}\n")
    with open(path, "r", encoding="utf-8") as f:
        lines = [json.loads(line) for line in f if line.strip()]

    if args.step is not None:
        for d in lines:
            if d.get("step_index") == args.step:
                print(f"=== STEP {d.get('step_index')} ({d.get('type')}) ===")
                content = str(d.get("content", ""))
                print(parse_nested_result(content))
                if d.get("tool_calls"):
                    print("TOOLS:", json.dumps(d.get("tool_calls"), ensure_ascii=False, indent=2))
        return

    for d in lines[-args.lines:]:
        idx = d.get("step_index")
        t = d.get("type")
        status = d.get("status")
        content = str(d.get("content", "")).replace("\n", " ")[:400]
        print(f"[Step {idx}] {t} ({status}): {content}")
        if d.get("tool_calls"):
            for tc in d.get("tool_calls"):
                print(f"  -> TOOL: {tc.get('name')} {str(tc.get('args', ''))[:200]}")

if __name__ == "__main__":
    main()
