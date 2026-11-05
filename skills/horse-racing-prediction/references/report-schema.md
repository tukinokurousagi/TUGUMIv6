# Report Schema & Persistence Rules

## Filename Conventions (TUGUMI Standard Rule 5)
- Format: `YYYYMMDD_{開催地}{レース番号}R_{レース名}_予想レポート.md`
- Example: `20260816_札幌11R_札幌記念_予想レポート.md` (Note: Venue, Race Num, Race Name are fully dynamic placeholders derived from user input).

## Report Output Directory (TUGUMI Standard Rule 6)
- Default path: `/storage/emulated/0/TUGUMIDesk/競馬予想/`
- Standard Markdown structure with UTF-8 encoding.

## Save Verification (Rule 26)
- The agent MUST call `mcp_horse_racing_report_save`.
- Only inform the user of successful save when `saved == true`.
