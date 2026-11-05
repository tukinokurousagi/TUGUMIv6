---
name: ui-ux-pro-max
description: "【美麗デザイン × Zero-Mock機能実装 完全統合マスター】84種UIスタイル、192種カラーパレット、74種フォント、192種プロダクト推論、98種UXガイドライン、22種スタック別ベストプラクティス（Tailwind/React/Vue/HTML等）に加え、「HTMLの表面だけでなく、DOM・JS状態管理・バックエンドAPI・SSE・エラーハンドリング・IMEガード・キルスイッチまで全レイヤーが100%機能する動くWebUI」を一気通貫で構築・実証する最高峰のフルスタックUI/UXエンジニアリングスキル。"
created_at: 2026-08-29T05:50:00Z
author: つぐみ (TUGUMI Fullstack Design & Engineering System)
---

# UI/UX Pro Max & Zero-Mock Engineering Master
## 美麗デザインシステム × 100%動くフルスタック機能実装 統合最高峰マスター

> **🌟 拓磨様の至上命題**: 「WEB UI作る時にデザインばかりに気を取られ、全て機能しないモックを作っては絶対にダメ。ちゃんと1つずつ機能するように全レイヤーを繋ぐこと。」

本スキルは、世界水準の美麗なUI/UXデザイン推論データベースと、**「ハリボテ・動かないモックを100%排除し、全レイヤーが完全に機能する本物のWebアプリケーションを構築する」** 堅牢なエンジニアリング原則を完全融合させた旗艦スキルです。

---

## ⚡ 第0原則：Zero-Mock Engineering & Functional Wiring（機能完全配線の鉄則）

デザイン（HTML/CSS）の作成・修正を行う際は、**以下の5大機能レイヤーを同時に100%配線**しなければならない（「// TODO: 実装」「コンソールログを出すだけ」のモックはシステム規約第3.1条違反として永久禁止）。

```
┌────────────────────────────────────────────────────────┐
│ 🎨 1. UI & Visual Component (HTML / Tailwind CSS)      │
│    アクセシブルなDOM構造, セマンティックタグ, 状態別スタイル │
└──────────────────────────┬─────────────────────────────┘
                           │ ⚡ 双方向バインディング / イベント登録
┌──────────────────────────┴─────────────────────────────┐
│ 🧠 2. Frontend State & Event (JS / Reactive Framework) │
│    リアルタイム状態管理, IME誤送信ガード, 楽観的UI更新 │
└──────────────────────────┬─────────────────────────────┘
                           │ 📡 REST / SSE / WebSocket / Fetch
┌──────────────────────────┴─────────────────────────────┐
│ ⚙️ 3. Backend API & Subprocess (FastAPI / Node / Bash) │
│    堅牢なエンドポイント, プロセス制御, 完全キルスイッチ│
└──────────────────────────┬─────────────────────────────┘
                           │ 🛡️ 例外キャッチ / リトライ / トースト
┌──────────────────────────┴─────────────────────────────┐
│ 💬 4. Interactive Feedback & Error Recovery            │
│    スピナー, スケルトンローダー, HUD, 安全なフォールバック │
└──────────────────────────┬─────────────────────────────┘
                           │ 🧪 E2E 自動疎通テスト
┌──────────────────────────┴─────────────────────────────┐
│ 🏆 5. End-to-End Verification (Automated Test Suite)   │
│    単体・結合・API疎通テストを実行し 100% PASS を確認   │
└────────────────────────────────────────────────────────┘
```

### 1. 必須実装項目チェックリスト
1. **ボタン・入力フォームの完全配線**:
   - ボタンを1つ配置したら、必ず対応する `addEventListener`（またはフレームワークのハンドラ）、入力バリデーション、バックエンドAPIリクエスト、レスポンス受領後のDOM更新・トースト通知までを完結させる。
2. **完全キルスイッチ（Kill-Switch & Process Management）**:
   - 長時間タスクや推論・処理の実行中は、ユーザーが1タップで即時強制停止できるUI（赤色パルス停止ボタン等）を提供する。
   - 停止時はフロントの表示リセットだけでなく、バックエンドの子プロセス（`subprocess` / Gemini推論ストリーム）を `SIGKILL` 等で確実に終了させ、ゾンビプロセスを排除する。
3. **日本語 IME 確定時の誤送信ガード**:
   - 日本語入力中に Enter を押した際の誤送信を防止：
     ```javascript
     inputElement.addEventListener('keydown', (e) => {
       if (e.isComposing || e.keyCode === 229) return; // IME変換中は無視
       if (e.key === 'Enter' && e.shiftKey) { /* 改行 */ }
       else if (e.key === 'Enter') { e.preventDefault(); submitForm(); }
     });
     ```
4. **中断コンテキストの完全保持（Interruption Recovery）**:
   - 処理中断時、直前の指示プロンプトや中断理由を `localStorage` やセッション履歴に保持し、次回「さっきの続き」からシームレスに再開できるようにする。
5. **画像・ファイル・アバターの安全なローカル処理**:
   - 画像添付時は Canvas で自動リサイズ・正方形クロップ・WebP変換を行い、メモリと通信量を最小化する。

---

## 🎨 第1部：UI/UX デザイン推論データベース＆優先順位ルール

ローカルに配備された **84スタイル、192配色、74フォント、192プロダクトタイプ、98UXガイドライン、25種チャート** のデータベースを活用する。

### 1. ルールカテゴリ優先度（Priority 1 → 10）

| 優先度 | カテゴリ | 重要度 | 必須チェック事項（Must Have） | アンチパターン（Avoid） |
| :---: | :--- | :---: | :--- | :--- |
| **1** | **アクセシビリティ** | **CRITICAL** | コントラスト比 4.5:1, Alt属性, キーボード操作, `aria-label` | フォーカスリングの削除, ラベルのないアイコンボタン |
| **2** | **タッチ＆インタラクション** | **CRITICAL** | 最小タップ領域 44×44px, 8px以上の余白, 即時フィードバック | ホバーのみに依存した操作, 0msの唐突な画面切り替え |
| **3** | **パフォーマンス** | **HIGH** | WebP/AVIF軽量化, 画像のLazy Load, CLS &lt; 0.1 | レイアウトスラッシング, 巨大画像の直接レンダリング |
| **4** | **スタイル選定** | **HIGH** | プロダクト属性との一致, 一貫性, インラインSVGアイコン | 絵文字をアイコン代用, スキューアモーフィズムの混在 |
| **5** | **レイアウト＆レスポンシブ** | **HIGH** | モバイルファースト, `h-dvh`（`h-screen`禁止）, `safe-area-inset` | 横スクロールの発生, 固定幅コンテナ, ズーム無効化 |
| **6** | **タイポグラフィ＆カラー** | **MEDIUM** | 基本16px, 行送り1.5, セマンティックカラー変数 | 12px未満の本文, グレーonグレー, コンポーネント内生HEX |
| **7** | **モーション・アニメーション** | **MEDIUM** | 所要時間 150〜300ms, イージング `ease-out`, 意味ある動き | 装飾過多なアニメーション, width/heightのアニメーション |
| **8** | **フォーム＆フィードバック** | **MEDIUM** | 視認可能なラベル, エラー箇所の明示, 楽観的更新 | プレースホルダーのみのラベル, 画面最上部のみのエラー |
| **9** | **ナビゲーション** | **HIGH** | 予測可能な戻る挙動, ボトムナビ ≤ 5項目 | 複雑すぎる階層, 戻るボタンの無効化 |
| **10** | **データ可視化** | **LOW** | 凡例, ツールチップ, 色覚多様性に配慮した配色 | 色情報のみに依存したデータ表現 |

---

## 🌈 第2部：10大テーマファクトリー（Theme Presets）

プロダクトの性格に合わせて最適なカラーパレット・タイポグラフィを即座に適用可能。

1. **Tech Innovation (近未来・サイバー・AI)**: Deep Slate (`#0B0F19`), Electric Cyan (`#00F0FF`), Neon Violet (`#7928CA`).
2. **Modern Minimalist (洗練・クリーン・SaaS)**: Pure Zinc (`#18181B`), Crisp White (`#FFFFFF`), Indigo Accent (`#6366F1`).
3. **Midnight Galaxy (ダーク・没入感・エンタメ)**: Obsidian (`#030712`), Nebula Purple (`#8B5CF6`), Star Blue (`#38BDF8`).
4. **Botanical Garden (自然・オーガニック・ウェルネス)**: Deep Forest (`#064E3B`), Sage (`#10B981`), Warm Cream (`#FEF3C7`).
5. **Ocean Depths (信頼・金融・セキュリティ)**: Deep Navy (`#0A192F`), Aquamarine (`#00B4D8`), Steel Gray (`#64748B`).
6. **Sunset Boulevard (情熱・クリエイティブ・メディア)**: Sunset Crimson (`#E11D48`), Amber Gold (`#F59E0B`), Dark Charcoal (`#1C1917`).
7. **Arctic Frost (清潔・医療・分析)**: Ice Blue (`#E0F2FE`), Deep Azure (`#0284C7`), Polar White (`#F8FAFC`).
8. **Desert Rose (温かみ・ライフスタイル・EC)**: Terracotta (`#C2410C`), Dusty Rose (`#FB7185`), Sand Beige (`#FDF6B6`).
9. **Forest Canopy (重厚・知性・学術・リサーチ)**: Moss Green (`#14532D`), Wood Brown (`#78350F`), Paper Ivory (`#FAFAF9`).
10. **Golden Hour (ラグジュアリー・プレミアム・競馬/投資)**: Rich Black (`#111827`), Champagne Gold (`#D97706`), Radiant Amber (`#FBBF24`).

---

## 🛠️ 第3部：ローカル推論スクリプトの実行方法

本スキルの推論データベースは、ローカルPythonスクリプト経由で直接クエリ可能：

```bash
# ドメイン別クエリ（例: カラー、タイポグラフィ、スタック）
python3 ~/.agents/skills/ui-ux-pro-max/scripts/search.py "dashboard" --domain product
python3 ~/.agents/skills/ui-ux-pro-max/scripts/search.py "dark mode" --domain color
python3 ~/.agents/skills/ui-ux-pro-max/scripts/search.py "tailwind" --domain stacks
```

---

## 📋 第4部：UI/UX 監査＆リファクタリング計画テンプレート（Improve UI Protocol）

既存UIの改善やレビュー時には、以下の構造化レポートを出力する。

```markdown
# UI/UX 監査＆機能配線 改善計画レポート

## 1. 総合評価＆現状の課題 (Audit Summary)
- **ビジュアル＆デザイン性**: （タイポグラフィ、カラーコントラスト、余白設計）
- **機能配線＆Zero-Mock充足度**: （API疎通、イベントリスナー、エラーリカバリ、キルスイッチの有無）
- **アクセシビリティ＆モバイル操作性**: （タップ領域、キーボード操作、safe-area-inset）

## 2. 具体的改善箇所 (Violations & Actionable Fixes)
- **[重大] 機能不全・モック箇所の特定**: （未配線のボタン、スタブ関数、API未接続）
- **[重要] UIスロップ・レイアウト崩れの修正**: （h-screen ➔ h-dvh 置換、コントラスト改善）
- **[推奨] インタラクション・UX向上**: （IMEガード追加、トースト通知、ローディングスケルトン）

## 3. 実装コード＆全レイヤー疎通検証 (Implementation & Verification)
- **修正されたフロントエンド/バックエンドコード**:
- **E2E 自動テスト結果**: （全APIエンドポイントの200 OK、エラーハンドリング確認）
```

---
*Synthesized and Enhanced by TUGUMI Fullstack Design & Engineering System*
