# Horse Racing Data Contract Specification (v1.0)

## Overview
This document defines the strict data contract between the Horse Racing MCP Server and LLM Agents (HermesAgent, TUGUMIv5, Antigravity CLI).

## Zero-Hallucination Principles
1. **Factual Integrity**: LLM MUST NOT guess horse_number, horse_name, odds, track condition, or jockey names.
2. **Strict Verification**: Every prediction output MUST validate horse number/name pairs against `mcp_horse_racing_validate`.
3. **Dynamic Resolution**: All parameters (venue, race_number, race_name, date) are resolved dynamically from user input requests.

## Exposed Tools
- `mcp_horse_racing_race_resolve` (date, venue, race_number, race_name) -> race_id
- `mcp_horse_racing_race_card` (race_id) -> list of runners
- `mcp_horse_racing_validate` (race_id, expected_runners, tickets) -> PASS / FAIL
- `mcp_horse_racing_horse_history` (horse_id) -> historical performances
- `mcp_horse_racing_market` (race_id) -> odds & popularity
- `mcp_horse_racing_race_context` (race_id) -> weather & track bias
- `mcp_horse_racing_report_save` (filename, content, directory) -> filesystem status & SHA-256
