---
name: gemini-model-guard
description: Gemini 3系モデル選定・フォールバック・自己修復の設計原則ガイド.
---

# Gemini Model Guard & Auto-Healing Hierarchy Specification

## When to Use
TUGUMIv5においてGeminiモデルの設定変更、APIエラー（500/503/429/400）のトラブルシューティング、自己修復機能（Auto-Heal）の保守・改修を行う際に必ず参照する。

## Prerequisites
- Google GenAI SDK (`google-genai`)
- 有効な `GEMINI_API_KEY`
- Gemini 3 ファミリー（`gemini-3.7-flash`, `gemini-3.5-flash`, `gemini-3.5-flash-lite`）

## Model Architecture Tier (絶対遵守ルール)

| 役割 | 採用モデル | 選定理由と特性 |
| :--- | :--- | :--- |
| **メイン推論エンジン** | `gemini-3.5-flash` | 高速・高安定性・確実なツール実行・503過負荷耐性・単一統合コア（Unified Core）。 |
| **一時的過負荷リカバリ** | 指数バックオフ再試行 | 503/429/一時的エラー発生時は指数バックオフ（最大5回）により同一モデルで安全に再試行。 |
| **自己修復 (Auto-Heal)** | `gemini-3.5-flash` | 安定稼働GAモデル。メイン一時負荷時にも道連れにならず確実にコードを修復。 |

> [!CAUTION]
> **旧世代（Gemini 2.5系）モデルの混用禁止**:
> `gemini-2.5-flash` 等の2.5系モデルは、Gemini 3系の `thought_signature`（暗号化推論状態トークン）および `ThinkingConfig` スキーマと互換性がなく、マルチターン会話履歴の引き継ぎ時に `400 INVALID_ARGUMENT` エラーを発生させます。モデルは一貫して `gemini-3.5-flash` 単一統合コアを使用すること。

## API Request & ThinkingConfig 仕様
- **ThinkingConfig**: `types.ThinkingConfig(include_thoughts=True)` または `thinking_level="low"` を使用する。Gemini 2.5用の `thinking_budget`（数値指定）はGemini 3系モデルでは使用しない。
- **Thought Signature**: FunctionCall に付随する `thought_signature` パートは、マルチターン会話履歴送信時に絶対に欠落・改変しないこと。

## Procedure
1. モデル設定を確認する際は、`main.py`, `web_server.py`, `tugumiv5_autoheal.py`, `gemini_client.py` の階層構造を確認する。
2. 推論コアおよび自己修復（`auto_heal_code`, `auto_heal_api_error`, `auto_investigate_error`）が `gemini-3.5-flash` に統一されていることを確認する。
3. 一時的な過負荷（503/429）に対しては指数バックオフによる自動再試行が機能することを確認する。
4. 単体テスト（`python -m unittest discover -s tests`）を実行し、全テストの通過を検証する。

## Pitfalls
- **自己修復に3.7-flashを割り当てない**: サーバー側の500/503過負荷時に自己修復ドクター自体が停止し共倒れになる。
- **2.5系モデルへの安易な差し戻しを行わない**: `thought_signature` 不整合による400エラーが再発する。

## Verification
```bash
python -c "
from memory_sqlite import MemoryDB
db = MemoryDB()
facts = db.search_facts('gemini')
print(facts)
"
```
