# Cyber HUD & Frame Decoration Reference

HUD frames turn standard ASCII art into high-tech dashboard banners, system launch headers, and security cards.

---

## 1. Frame Styles Overview

### A. `cyber_hud` (High-Tech Rounded HUD)
Features rounded corner connectors, a top title capsule, optional subtitle divider, and a bottom status chevron telemetry bar.

```text
╭─[ TUGUMI v5.0 // RED_CYBER ]─────────╮
│  Autonomous AI Agent Core             │
├───────────────────────────────────────┤
│   ________  __________  ____  _______ │
│  /_  __/ / / / ____/ / / /  |/  /  _/ │
│   / / / / / / / __/ / / / /|_/ // /   │
│  / / / /_/ / /_/ / /_/ / /  / // /    │
│ /_/  \____/\____/\____/_/  /_/___/    │
╰────────────────────❯ STATUS: ONLINE ─╯
```

### B. `double_box` (Double-Line Classical Border)
Solid, formal, commanding presence.

```text
╔══════════════════════════════════════╗
║  SECURITY AUDIT REPORT 2026          ║
╠══════════════════════════════════════╣
║                                      ║
║   _____ ______ _____ _   _ _____     ║
║  / ____|  ____/ ____| | | |  __ \    ║
║ | (___ | |__ | |    | | | | |__) |   ║
║  \___ \|  __|| |    | | | |  _  /    ║
║  ____) | |___| |____| |_| | | \ \    ║
║ |_____/|______\_____|\___/|_|  \_\   ║
║                                      ║
╚══════════════════════════════════════╝
```

### C. `heavy_box` (Bold Solid Border)
Heavy industrial look.

```text
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                                      ┃
┃   _______  ______ _____              ┃
┃  |__   __|/ __  // ____|             ┃
┃     | |  | |  | | |                  ┃
┃     | |  | |  | | |                  ┃
┃     | |  | |__| | |____              ┃
┃     |_|   \____/ \_____|             ┃
┃                                      ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

### D. `neon_bracket` (Mechanical Cyber Brackets)
Low visual weight, high aesthetic style.

```text
【 ❖ ───────────────────────────────── ❖ 】
    ____  ______ _____  ____  ____ _____   
   / __ \/ ____// ___/ / __ \/ __ / ___/   
  / /_/ / __/   \__ \ / /_/ / / / \__ \    
 / ____/ /___  ___/ // ____/ /_/ ___/ /    
/_/   /_____/ /____//_/    \____/____/     
【 ❖ ───────────────────────────────── ❖ 】
```

### E. `minimal_line` (Clean Accent Border)
```text
────────────────────────────────────────
  ________  ______ __  ____  ________   
 /_  __/ / / / __ / / / /  |/  /  _/    
  / / / /_/ / /_/ / /_/ / /|_/ // /     
 /_/  \____/\____/\____/_/  /_/___/     
────────────────────────────────────────
```

---

## 2. Dynamic Telemetry & Status Badges
You can customize footer status badges:
*   `STATUS: ONLINE` (Standard operational state)
*   `STATUS: ACTIVE` (Processing live tasks)
*   `STATUS: LOCKED` (AES-GCM encrypted mode)
*   `STATUS: SECURE` (Defense layer active)
*   `STATUS: 0 ERRORS` (Audit PASS)
