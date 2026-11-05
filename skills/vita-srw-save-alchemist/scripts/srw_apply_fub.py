#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SRW X Full Upgrade Bonus & 10-Step Upgrade Applier (Robust Edition)
Upgrades all active mechs to 10-step Full Upgrade status, enabling the +1 Power Parts Slot bonus.
Preserves existing weapons upgrades (>10) and equipped parts.
Handles in-battle buffs/parts where current HP or EN may exceed basic max values.
Recalculates save checksums via save-editor API.
"""

import sys
import os
import struct
import shutil
from srw_checksum import fix_checksum

def apply_fub_to_save(file_path: str, save_type: str) -> bool:
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False

    with open(file_path, "rb") as f:
        data = bytearray(f.read())

    stride = 0x88
    modified_mechs = 0
    print(f"[{save_type}] Scanning for active mechs to apply 10-step Full Upgrade...")

    for addr in range(0x2000, 0x40000, 4):
        if addr + stride > len(data):
            break

        chunk = data[addr:addr+stride]
        flag = int.from_bytes(chunk[8:12], "little")
        hp = int.from_bytes(chunk[0x34:0x38], "little")
        hp_max = int.from_bytes(chunk[0x38:0x3c], "little")
        en = int.from_bytes(chunk[0x3c:0x3e], "little")
        en_max = int.from_bytes(chunk[0x3e:0x40], "little")

        # Validate mech header: allows for in-battle buffs where en or hp can temporarily exceed basic max
        if 2000 < hp_max < 35000 and 0 < hp < 35000 and 50 < en_max < 1500 and 0 < en < 1500:
            upgrades = list(chunk[0x10:0x16])
            if all(0 <= u <= 15 for u in upgrades):
                old_upgrades = list(upgrades)
                old_hp_max = hp_max
                old_en_max = en_max

                # Calculate upgrade delta
                # Base 5 stats: HP, EN, Aim, Mobility, Armor
                hp_step_diff = max(0, 10 - upgrades[0])
                en_step_diff = max(0, 10 - upgrades[1])
                aim_step_diff = max(0, 10 - upgrades[2])
                mob_step_diff = max(0, 10 - upgrades[3])
                arm_step_diff = max(0, 10 - upgrades[4])

                # Set all basic 5 stats to 10
                for k in range(5):
                    upgrades[k] = 10
                # Weapon: max(current, 10)
                upgrades[5] = max(upgrades[5], 10)

                # Write back upgrades
                data[addr+0x10:addr+0x16] = bytes(upgrades)

                # Update stats values
                # HP per step = +250
                hp_increase = hp_step_diff * 250
                new_hp_max = hp_max + hp_increase
                new_hp = hp + hp_increase
                data[addr+0x34:addr+0x38] = struct.pack("<I", new_hp)
                data[addr+0x38:addr+0x3c] = struct.pack("<I", new_hp_max)

                # EN per step = +10
                en_increase = en_step_diff * 10
                new_en_max = en_max + en_increase
                new_en = en + en_increase
                data[addr+0x3c:addr+0x3e] = struct.pack("<H", new_en)
                data[addr+0x3e:addr+0x40] = struct.pack("<H", new_en_max)

                # Aim per step = +3
                aim = int.from_bytes(chunk[0x16:0x18], "little") + aim_step_diff * 3
                data[addr+0x16:addr+0x18] = struct.pack("<H", aim)

                # Mobility per step = +3
                mob = int.from_bytes(chunk[0x18:0x1a], "little") + mob_step_diff * 3
                data[addr+0x18:addr+0x1a] = struct.pack("<H", mob)

                # Armor per step = +30
                arm = int.from_bytes(chunk[0x1a:0x1c], "little") + arm_step_diff * 30
                data[addr+0x1a:addr+0x1c] = struct.pack("<H", arm)

                # Ensure Full Upgrade & Custom Bonus active flag (0x1000001)
                new_flag = flag | 0x01000001
                data[addr+8:addr+12] = struct.pack("<I", new_flag)

                p1 = int.from_bytes(chunk[0x40:0x44], "little")
                p2 = int.from_bytes(chunk[0x44:0x48], "little")
                p3 = int.from_bytes(chunk[0x48:0x4c], "little")
                p4 = int.from_bytes(chunk[0x4c:0x50], "little")

                modified_mechs += 1
                print(f"  Mech @ 0x{addr:x}: Upgrades {old_upgrades} -> {upgrades}, HP_max: {old_hp_max}->{new_hp_max}, EN_max: {old_en_max}->{new_en_max}, Parts=[{p1},{p2},{p3},{p4}]")

    print(f"[{save_type}] Successfully applied Full Upgrade to {modified_mechs} mechs!")

    # Write back modified binary
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
    stg_file = "/storage/emulated/0/PSvita/ux0/user/00/savedata/PCSG01128/PCSG01128-STG-001/STAGE.BIN"
    sys_file = "/storage/emulated/0/PSvita/ux0/user/00/savedata/PCSG01128/PCSG01128-SYS/SYSTEM.BIN"

    print("=== Super Robot Wars X: Applying Full Upgrade & +1 Parts Slot ===")
    ok1 = apply_fub_to_save(stg_file, "STAGE")
    ok2 = apply_fub_to_save(sys_file, "SYSTEM")

    if ok1 and ok2:
        print("=== ALL SAVES SUCCESSFULLY UPDATED TO FULL UPGRADE (+1 PARTS SLOT READY)! ===")
        sys.exit(0)
    else:
        print("=== ERROR: Update failed! ===")
        sys.exit(1)
