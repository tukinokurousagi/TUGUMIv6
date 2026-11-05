#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SRW Save Alchemist (NG+ Transfer & Asset Injection Tool)
Ports kills, power-up parts, magic customization, funds, and TacP from clear data to NG+ save.
"""

import sys
import os
import struct
import shutil
from srw_checksum import fix_checksum

def transfer_ng_plus(src_path: str, dst_path: str, funds: int = 50000000, tacp: int = 300000) -> bool:
    if not os.path.exists(src_path) or not os.path.exists(dst_path):
        print(f"Error: Missing files. src={src_path}, dst={dst_path}")
        return False

    # Backup destination
    shutil.copyfile(dst_path, dst_path + ".bak_alchemist")

    src_data = bytearray(open(src_path, "rb").read())
    dst_data = bytearray(open(dst_path, "rb").read())

    # 1. Kills (Score) Transfer
    # Map PID -> Score from src
    pid_score_map = {}
    for i in range(0xca):
        addr = 0xbd70 + i * 0x1f8
        pid = int.from_bytes(src_data[addr:addr+2], "little")
        score = int.from_bytes(src_data[addr+6:addr+8], "little")
        if pid > 0 and score > 0:
            pid_score_map[pid] = max(pid_score_map.get(pid, 0), score)

    applied_kills = 0
    for i in range(0xca):
        addr = 0xbd70 + i * 0x1f8
        pid_dst = int.from_bytes(dst_data[addr:addr+2], "little")
        if pid_dst > 0:
            old_score = int.from_bytes(dst_data[addr+6:addr+8], "little")
            past_kills = pid_score_map.get(pid_dst, 0)
            dst_data[addr+6:addr+8] = struct.pack("<H", old_score + past_kills)
            applied_kills += past_kills
        else:
            pid_src = int.from_bytes(src_data[addr:addr+2], "little")
            score_src = int.from_bytes(src_data[addr+6:addr+8], "little")
            if pid_src > 0 and score_src > 0:
                dst_data[addr:addr+2] = struct.pack("<H", pid_src)
                dst_data[addr+6:addr+8] = struct.pack("<H", score_src)
                applied_kills += score_src

    print(f"[Alchemist] Applied {applied_kills} kills across all pilot rosters.")

    # 2. Magic Customization Flags (0x4f0 - 0x530)
    dst_data[0x4f0:0x510] = src_data[0x4f0:0x510]
    dst_data[0x51f:0x530] = src_data[0x51f:0x530]
    print("[Alchemist] Magic customization GRADE flags synchronized.")

    # 3. Power-Up Parts Inventory (0x658 - 0xec8, 90 parts, 24 bytes stride)
    unlocked_parts = 0
    for i in range(0x5a):
        addr = 0x658 + i * 0x18
        count = src_data[addr]
        if count > 0 and count != 0xff:
            part_count = max(count, 3) # Provide at least 3 for multi-unit equipping
            dst_data[addr] = part_count
            dst_data[addr+1] = 0 # Byte 1 = Equipped Count -> 0 = ALL FREE TO EQUIP
            dst_data[addr+2] = 0
            dst_data[addr+3] = 0
            dst_data[addr+4] = 1 # Unlocked
            unlocked_parts += 1

    print(f"[Alchemist] Unlocked {unlocked_parts} power-up parts with 0 equipped state (free stock).")

    # 4. Funds & TacP
    dst_data[0x440:0x444] = struct.pack("<I", funds)
    dst_data[0x444:0x448] = struct.pack("<I", funds + 12849276)
    dst_data[0x458:0x45c] = struct.pack("<I", tacp)
    dst_data[0x45c:0x460] = struct.pack("<I", tacp + 54691)

    # 5. Clear Count & Perks
    dst_data[0x51b] = 1 # Clear count 1
    dst_data[0x51c] = 31 # SR points
    dst_data[0x51e] = 1 # 15-step upgrade unlocked
    print(f"[Alchemist] Funds={funds:,}, TacP={tacp:,}, ClearCount=1, 15-step upgrade=ON.")

    # Write modified bytes
    with open(dst_path, "wb") as f:
        f.write(dst_data)

    # Fix checksum
    print("[Alchemist] Fixing checksum...")
    return fix_checksum(dst_path, "STAGE")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: srw_alchemist.py <src_clear_save> <dst_target_save> [funds] [tacp]")
        sys.exit(1)
    src = sys.argv[1]
    dst = sys.argv[2]
    f_val = int(sys.argv[3]) if len(sys.argv) > 3 else 50000000
    t_val = int(sys.argv[4]) if len(sys.argv) > 4 else 300000
    ok = transfer_ng_plus(src, dst, f_val, t_val)
    sys.exit(0 if ok else 1)
