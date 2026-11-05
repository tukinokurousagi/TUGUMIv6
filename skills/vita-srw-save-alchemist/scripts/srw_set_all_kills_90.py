#!/usr/bin/env python3
"""
SRW X All Pilots Kills Setter (Sets all active pilots' kill count to >= target, default 90)
Applies to both quicksave (SYSTEM.BIN) and normal stage save (STAGE.BIN).
"""

import os
import struct
import sys

from srw_checksum import fix_checksum


def set_kills(file_path: str, save_type: str, target_kills: int = 90) -> bool:
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False

    with open(file_path, "rb") as f:
        data = bytearray(f.read())

    # Verified offsets: STAGE.BIN = 0xbd70, SYSTEM.BIN (quicksave) = 0x44c38
    if save_type.upper() == "SYSTEM":
        base_addr = 0x44c38
    else:
        base_addr = 0xbd70

    stride = 0x1f8
    max_slots = 202
    modified_count = 0
    total_active = 0
    print(f"[{save_type}] Modifying pilots starting at 0x{base_addr:x} with min target kills = {target_kills}...")

    for i in range(max_slots):
        addr = base_addr + i * stride
        if addr + stride > len(data):
            break

        pid = struct.unpack_from("<H", data, addr)[0]
        lvl = data[addr+2]
        exp = struct.unpack_from("<H", data, addr+4)[0]
        old_score = struct.unpack_from("<H", data, addr+6)[0]

        # Active pilot check: valid PID or non-zero Level, Score, or Exp
        if pid > 0 or lvl > 0 or old_score > 0 or exp > 0:
            total_active += 1
            if old_score < target_kills:
                struct.pack_into("<H", data, addr+6, target_kills)
                modified_count += 1
                if modified_count <= 10 or old_score < 20:
                    print(f"  Slot {i:3d} (PID {pid:3d}, Lv {lvl:3d}): {old_score:3d} -> {target_kills} kills @ 0x{addr+6:x}")

    print(f"[{save_type}] Total valid pilots: {total_active}, Modified (< {target_kills}): {modified_count}")

    with open(file_path, "wb") as f:
        f.write(data)

    print(f"[{save_type}] Recalculating checksum via API...")
    ok = fix_checksum(file_path, save_type)
    if ok:
        print(f"[{save_type}] Checksum fixed successfully!")
    else:
        print(f"[{save_type}] Failed to fix checksum!")
    return ok

if __name__ == "__main__":
    kills = int(sys.argv[1]) if len(sys.argv) > 1 else 90

    stg_file = "/storage/emulated/0/PSvita/ux0/user/00/savedata/PCSG01128/PCSG01128-STG-001/STAGE.BIN"
    sys_file = "/storage/emulated/0/PSvita/ux0/user/00/savedata/PCSG01128/PCSG01128-SYS/SYSTEM.BIN"

    print(f"=== Super Robot Wars X: Setting All Pilots Kills to >= {kills} ===")
    ok1 = set_kills(stg_file, "STAGE", kills)
    ok2 = set_kills(sys_file, "SYSTEM", kills)

    if ok1 and ok2:
        print(f"=== ALL SAVES SUCCESSFULLY UPDATED TO >= {kills} KILLS! ===")
        sys.exit(0)
    else:
        print("=== ERROR: One or more saves failed to update! ===")
        sys.exit(1)
