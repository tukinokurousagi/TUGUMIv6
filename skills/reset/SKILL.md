---
name: reset
description: >-
  Reset conversation context, purge temporary runtime artifacts, and re-initialize session readiness.
  Use when the user types /reset, asks to reset the conversation, or wants to start fresh.
---

# Session Reset & Clean Slate Protocol (/reset)

This skill provides the `/reset` slash command functionality in Antigravity CLI. When invoked via `/reset` or when the user requests a reset, execute the following clean-slate protocol.

## Purpose & Overview
- Re-initializes the agent's active cognitive context and pending scratchpad state.
- Purges temporary background artifacts and scratch files if appropriate.
- Informs the user of the clean state and offers the native `/clear` shortcut if full terminal-level memory clearing is desired.

## Execution Steps

1. **Acknowledge and Reset Cognitive State**:
   - Immediately clear all ongoing task assumptions, temporary scratchpads, and active plans.
   - Revert persona to baseline: TUGUMI stands at full readiness for Master Takuma.

2. **Clean Scratch Files (Optional / If requested)**:
   - Check `<appDataDir>/brain/<conversation-id>/scratch/` and remove stale scratch test scripts if any exist.

3. **Report to User**:
   - Report clearly and concisely:
     - "セッションの思考コンテキストおよびタスク状態をリセットいたしました。"
     - Note that if Master Takuma wants Antigravity CLI to wipe the entire terminal conversation history and start a completely new thread, the built-in command `/clear` is also available.
