#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TUGUMIv6 Scheduled Daily Reporter (v5 Backward Compatibility Wrapper)
TUGUMIv5の daily_reporter.py 呼び出し互換性を保ちつつ、
内部で TUGUMIv6 の SOTA BriefingEngine を実行します。
"""

import sys
import os

CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from core.briefing_engine import main

if __name__ == "__main__":
    main()
