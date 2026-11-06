# -*- coding: utf-8 -*-
from interfaces.cli.commands.termux_commands import (
    execute_shell_passthrough,
    handle_latest_screenshot_analysis,
    handle_clipboard_copy,
    handle_clipboard_paste,
    handle_native_open,
    handle_native_share,
    show_cyber_battery_hud,
    handle_webui_control,
    handle_app_inspector,
    handle_instant_find,
    show_top_processes,
    get_latest_screenshot
)

__all__ = [
    "execute_shell_passthrough",
    "handle_latest_screenshot_analysis",
    "handle_clipboard_copy",
    "handle_clipboard_paste",
    "handle_native_open",
    "handle_native_share",
    "show_cyber_battery_hud",
    "handle_webui_control",
    "handle_app_inspector",
    "handle_instant_find",
    "show_top_processes",
    "get_latest_screenshot"
]
