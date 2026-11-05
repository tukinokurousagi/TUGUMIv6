#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SRW Checksum Fixer (PS Vita / PC STAGE.BIN & SYSTEM.BIN)
Connects to save-editor.com checksum recalculation API.
"""

import sys
import os
import uuid
import urllib.request

def fix_checksum(file_path: str, save_type: str = "STAGE") -> bool:
    if not os.path.exists(file_path):
        print(f"Error: File not found: {file_path}")
        return False

    with open(file_path, "rb") as f:
        data = f.read()

    title_id = "SuperRobotWarsX_SYSTEM" if save_type.upper() == "SYSTEM" else "SuperRobotWarsX"
    filename = "SYSTEM.BIN" if save_type.upper() == "SYSTEM" else "STAGE.BIN"

    url = "https://save-editor.com/tool/wse_checksum_pc_game_output.cgi"
    boundary = "----WebKitFormBoundary" + uuid.uuid4().hex

    body = bytearray()
    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="lang"\r\n\r\nen\r\n'.encode('utf-8'))
    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="checksum_console"\r\n\r\npc\r\n'.encode('utf-8'))
    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="select_title_pc"\r\n\r\n{title_id}\r\n'.encode('utf-8'))
    body.extend(f'--{boundary}\r\nContent-Disposition: form-data; name="upload_save"; filename="{filename}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode('utf-8'))
    body.extend(data)
    body.extend(b'\r\n')
    body.extend(f'--{boundary}--\r\n'.encode('utf-8'))

    req = urllib.request.Request(url, data=bytes(body), headers={
        "User-Agent": "Mozilla/5.0",
        "Content-Type": f"multipart/form-data; boundary={boundary}",
        "Referer": "https://save-editor.com/tool/wse_checksum_pc_game.html"
    })

    try:
        fixed_data = urllib.request.urlopen(req, timeout=30.0).read()
        if len(fixed_data) != len(data):
            print(f"Error: Returned data length mismatch: {len(fixed_data)} vs {len(data)}")
            return False

        with open(file_path, "wb") as f:
            f.write(fixed_data)
        print(f"Checksum fixed successfully! New checksum: {fixed_data[:4].hex()}")
        return True
    except Exception as e:
        print(f"Error contacting checksum API: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: srw_checksum.py <save_file_path> [STAGE|SYSTEM]")
        sys.exit(1)
    target = sys.argv[1]
    stype = sys.argv[2] if len(sys.argv) > 2 else ("SYSTEM" if "SYS" in target.upper() else "STAGE")
    success = fix_checksum(target, stype)
    sys.exit(0 if success else 1)
