#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SRW X 15-Step Full Max Upgrade Applier
Upgrades all active mechs to the absolute limit: 15-step MAX for ALL categories
(HP, EN, Aim, Mobility, Armor, Weapons).
Recalculates save checksums via save-editor API.
"""

import sys
import os
import struct
from srw_checksum import fix_checksum

def apply_15_step_max(file_path: str, save_type: str) -> bool:
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False

    with open(file_path, "rb") as f:
        data = bytearray(f.read())

    stride = 0x88
    modified_mechs = 0
    print(f"[{save_type}] Applying 15-step MAX Upgrade to all active mechs...")

    for addr in range(0x2000, 0x40000, 4):
        if addr + stride > len(data):
            break

        chunk = data[addr:addr+stride]
        flag = int.from_bytes(chunk[8:12], "little")
        hp = int.from_bytes(chunk[0x34:0x38], "little")
        hp_max = int.from_bytes(chunk[0x38:0x3c], "little")
        en = int.from_bytes(chunk[0x3c:0x3e], "little")
        en_max = int.from_bytes(chunk[0x3e:0x40], "little")

        if 2000 < hp_max < 35000 and 0 < hp < 35000 and 50 < en_max < 1500 and 0 < en < 1500:
            upgrades = list(chunk[0x10:0x16])
            if all(0 <= u <= 15 for u in upgrades):
                old_upgrades = list(upgrades)
                old_hp_max = hp_max
                old_en_max = en_max

                # Steps to 15
                hp_diff = 15 - upgrades[0]
                en_diff = 15 - upgrades[1]
                aim_diff = 15 - upgrades[2]
                mob_diff = 15 - upgrades[3]
                arm_diff = 15 - upgrades[4]

                # Set ALL 6 categories to 15
                for k in range(6):
                    upgrades[k] = 15

                data[addr+0x10:addr+0x16] = bytes(upgrades)

                # Stats adjustments to 15-step
                new_hp_max = hp_max + hp_diff * 250
                new_hp = hp + hp_diff * 250
                data[addr+0x34:addr+0x38] = struct.pack("<I", new_hp)
                data[addr+0x38:addr+0x3c] = struct.pack("<I", new_hp_max)

                new_en_max = en_max + en_diff * 10
                new_en = en + en_diff * 10
                data[addr+0x3c:addr+0x3e] = struct.pack("<H", new_en)
                data[addr+0x3e:addr+0x40] = struct.pack("<H", new_en_max)

                aim = int.from_bytes(chunk[0x16:0x18], "little") + aim_diff * 3
                data[addr+0x16:addr+0x18] = struct.pack("<H", aim)

                mob = int.from_bytes(chunk[0x18:0x1a], "little") + mob_diff * 3
                data[addr+0x18:addr+0x1a] = struct.pack("<H", mob)

                arm = int.from_bytes(chunk[0x1a:0x1c], "little") + arm_diff * 30
                data[addr+0x1a:addr+0x1c] = struct.pack("<H", arm)

                # Ensure Full Upgrade & Custom Bonus active flag (0x1000001)
                new_flag = flag | 0x01000001
                data[addr+8:addr+12] = struct.pack("<I", new_flag)

                modified_mechs += 1
                print(f"  Mech @ 0x{addr:x}: Upgrades {old_upgrades} -> [15, 15, 15, 15, 15, 15] (MAX), HP: {new_hp}, EN: {new_en}")

    print(f"[{save_type}] Upgraded {modified_mechs} mechs to 15-step MAX!")

    with open(file_path, "wb") as f:
        f.write(data)

    print(f"[{save_type}] Recalculating checksum via API...")
    return fix_checksum(file_path, save_type)

if __name__ == "__main__":
    stg_file = "/storage/emulated/0/PSvita/ux0/user/00/savedata/PCSG01128/PCSG01128-STG-001/STAGE.BIN"
    sys_file = "/storage/emulated/0/PSvita/ux0/user/00/savedata/PCSG01128/PCSG01128-SYS/SYSTEM.BIN"

    print("=== Super Robot Wars X: Upgrading ALL Mechs to 15-Step MAX ===")
    ok1 = apply_15_step_max(stg_file, "STAGE")
    ok2 = apply_15_step_max(sys_file, "SYSTEM")

    if ok1 and ok2:
        print("=== ALL SAVES SUCCESSFULLY UPDATED TO 15-STEP MAX! ===")
        sys.exit(0)
    else:
        print("=== ERROR: Update failed! ===")
        sys.exit(1)
