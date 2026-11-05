#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SRW X Great Ace & Kills Injector
Guarantees all pilots achieve Great Ace status (minimum 100 kills)
while preserving top 1st-playthrough kill records (up to 218 kills).
"""

import sys
import os
import struct
import shutil
from srw_checksum import fix_checksum

def inject_great_ace(orig_path: str, target_path: str, min_kills: int = 100) -> bool:
    if not os.path.exists(orig_path) or not os.path.exists(target_path):
        print(f"Error: Missing files. orig={orig_path}, target={target_path}")
        return False

    with open(orig_path, "rb") as f:
        orig = bytearray(f.read())

    with open(target_path, "rb") as f:
        curr = bytearray(f.read())

    # 1. Map PID -> max score in orig
    orig_scores = {}
    for i in range(250):
        addr = 0xbd70 + i * 0x1f8
        if addr + 0x1f8 > len(orig):
            break
        pid = int.from_bytes(orig[addr:addr+2], "little")
        score = int.from_bytes(orig[addr+6:addr+8], "little")
        if 0 < pid < 1000 and 0 < score < 10000:
            orig_scores[pid] = max(orig_scores.get(pid, 0), score)

    print(f"[Injector] Loaded {len(orig_scores)} pilot kill records from 1st playthrough.")

    # 2. Iterate through current save pilot slots
    modified_count = 0
    total_injected_kills = 0
    for i in range(250):
        addr = 0xbd70 + i * 0x1f8
        if addr + 0x1f8 > len(curr):
            break

        pid_curr = int.from_bytes(curr[addr:addr+2], "little")
        lvl_curr = curr[addr+2]
        curr_score = int.from_bytes(curr[addr+6:addr+8], "little")

        # Also check orig at same slot
        pid_orig = int.from_bytes(orig[addr:addr+2], "little") if addr + 0x1f8 <= len(orig) else 0

        effective_pid = pid_curr if pid_curr > 0 else pid_orig

        if effective_pid > 0 or lvl_curr > 0:
            past_record = orig_scores.get(effective_pid, 0)
            target_score = max(min_kills, past_record, curr_score)

            if pid_curr == 0 and effective_pid > 0:
                curr[addr:addr+2] = struct.pack("<H", effective_pid)

            curr[addr+6:addr+8] = struct.pack("<H", target_score)
            modified_count += 1
            total_injected_kills += target_score
            # print first 15 modified
            if modified_count <= 15:
                print(f"  Slot {i:3d} (PID {effective_pid:3d}): {curr_score} -> {target_score} kills")

    print(f"[Injector] Successfully updated {modified_count} pilot slots (Total kills: {total_injected_kills:,}).")

    # 3. Write back modified save data
    with open(target_path, "wb") as f:
        f.write(curr)

    # 4. Checksum fix
    print("[Injector] Recalculating checksum via API...")
    return fix_checksum(target_path, "STAGE")

if __name__ == "__main__":
    orig_file = sys.argv[1] if len(sys.argv) > 1 else "/storage/emulated/0/PSvita/savedata_backup_SRWX/PCSG01128/PCSG01128-STG-001/STAGE.BIN"
    target_file = sys.argv[2] if len(sys.argv) > 2 else "/storage/emulated/0/PSvita/ux0/user/00/savedata/PCSG01128/PCSG01128-STG-001/STAGE.BIN"
    threshold = int(sys.argv[3]) if len(sys.argv) > 3 else 100

    ok = inject_great_ace(orig_file, target_file, threshold)
    sys.exit(0 if ok else 1)
