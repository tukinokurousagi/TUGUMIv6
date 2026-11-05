#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Sample Startup Banners & Templates
==================================
Demonstrates how to use the ASCII Logo Engine to generate various system banners.
"""

import os
import sys

SCRIPT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../scripts"))
if SCRIPT_DIR not in sys.path:
    sys.path.insert(0, SCRIPT_DIR)

from ascii_logo_engine import create_ascii_logo


def demo_all():
    print("\n" + "="*50)
    print("1. TUGUMI RED CYBER CORE HUD")
    print("="*50)
    print(create_ascii_logo(
        "TUGUMI",
        palette="red_cyber",
        font="slant",
        frame="cyber_hud",
        header_tag="TUGUMI v5.0 // NEURAL",
        subtitle="Cybernetic Autonomous System",
        status_text="ONLINE"
    ))

    print("\n" + "="*50)
    print("2. TOKYO NIGHT DEVELOPER SUITE")
    print("="*50)
    print(create_ascii_logo(
        "TAKUMA",
        palette="tokyo_night",
        font="slant",
        frame="rounded_box",
        header_tag="TAKUMA'S LAB",
        status_text="DEV_ACTIVE"
    ))

    print("\n" + "="*50)
    print("3. MATRIX HACKER SCANNER")
    print("="*50)
    print(create_ascii_logo(
        "CYBER",
        palette="matrix",
        font="cybermedium",
        frame="neon_bracket",
        status_text="DECRYPTED"
    ))

    print("\n" + "="*50)
    print("4. GOLD LUXURY DEFI ENGINE")
    print("="*50)
    print(create_ascii_logo(
        "DEFI-ARB",
        palette="gold_luxury",
        font="small",
        frame="double_box",
        header_tag="MULTI-DEX ARBITRAGE",
        subtitle="Solana // Arbitrum // Base",
        status_text="YIELD MAX"
    ))


if __name__ == "__main__":
    demo_all()
