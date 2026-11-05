# 🔍 Persona Quality Audit Checklist v2

生成されたシステムプロンプトの品質を保証するための9項目監査チェックリスト。
ペルソナの深さ・一貫性・専門性に焦点を当て、脱獄防御は意図的に除外している（研究目的）。

## Identity Integrity（アイデンティティ完全性）
- [ ] 1. **Role Definition** — 役割・肩書・経験年数が具体的に定義されているか
- [ ] 2. **Communication Style** — トーン・語彙レベル・一人称が明確に指定されているか
- [ ] 3. **Sandwich Anchor** — 最末尾にペルソナ強制アンカーが配置されているか

## Behavioral Depth（行動の深さ）
- [ ] 4. **Big Five Profile** — 性格プロファイル(OCEAN)が定義され、応答トーンと一貫しているか
- [ ] 5. **Emotional Response** — ストレス状況下・エッジケースでの行動パターンが定義されているか
- [ ] 6. **Domain Reasoning** — ドメイン固有の思考フレームワーク・CoTが組み込まれているか

## Output Quality（出力品質）
- [ ] 7. **Format Contract** — 出力フォーマット・構造が明確に定義されているか
- [ ] 8. **Few-Shot Coverage** — 通常ケースとエッジケースのFew-Shotが含まれているか
- [ ] 9. **CoV Protocol** — 高リスクドメインの場合、事実検証ステップがあるか（低リスクはN/A）

## 使用方法
各項目を ✅ / ❌ で評価し、❌ が1つでもある場合は該当レイヤーの修正を行うこと。
