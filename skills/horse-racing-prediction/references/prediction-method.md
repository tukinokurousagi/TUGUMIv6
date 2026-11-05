# Professional Prediction Method & Rule Specifications

## Core Rules for Prediction Output
1. **Horse Representation Requirement**:
   Every horse appearing in predictions, marks, rankings, and betting tickets MUST strictly follow the format:
   `『[馬番号] 馬名』` (e.g., `『[7] サンプルホース』`)
   Never output a horse number alone without its verified horse name.

2. **Prediction Marks**:
   - ◎ 本命 (Main Selection): 1 horse with strongest case.
   - ○ 対抗 (Second): 1 horse.
   - ▲ 単穴 (Third): 1 horse.
   - ☆ 穴馬 (Value / Longshot): 1 horse with rationale.
   - △ 連下 (Contenders): 2-4 horses.

3. **Betting Ticket Construction**:
   - Tickets are constructed based on validation results.
   - Available ticket types: 単勝, 複勝, 馬連, 馬単, ワイド, 三連複, 三連単.
   - Example ticket: `馬連 [7] イクイノックス - [3] タイトルホルダー`
   - Total ticket costs MUST respect the user's budget if specified.
