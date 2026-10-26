import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import re
import unittest
from collections import Counter

from interfaces.cli.main import is_image_creation_intent, is_music_creation_intent
from interfaces.web.web_server import (
    _is_system_health_query,
    is_music_creation_intent as web_is_music_intent,
    is_image_creation_intent as web_is_image_intent,
)

ROOT_DIR = Path(__file__).resolve().parent.parent


class TestCliWebUiBugfixAndHygiene(unittest.TestCase):
    def test_music_intent_unification_and_false_positive_prevention(self):
        # CLI and Web UI must share the exact same function
        self.assertIs(is_music_creation_intent, web_is_music_intent)
        self.assertIs(is_image_creation_intent, web_is_image_intent)

        # False positive cases that previously misfired due to 'インストール' -> 'インスト' + '作成'
        false_cases = [
            "タスクの内容の精度を上げる為なら必要なツールやパッケージをインストールし使用し、スクリプトやSKILL、MCPなども自由に作成し最高精度でタスクを完遂してくれ。",
            "パッケージをインストールしてBGM用のスクリプトを作成して",
            "音楽再生用のPythonコードを作成してバグを修正して",
            "/music create test",
        ]
        for text in false_cases:
            self.assertFalse(is_music_creation_intent(text), f"Should be False: {text}")

        # True positive cases
        true_cases = [
            "サイバーパンクなBGMを作って",
            "疾走感のあるインスト曲を作成して",
            "切ないメロディの歌を作曲して",
            "こんな形で楽曲お願い",
        ]
        for text in true_cases:
            self.assertTrue(is_music_creation_intent(text), f"Should be True: {text}")

    def test_image_intent_false_positive_prevention(self):
        false_cases = [
            "AIモデルを作成して推論テストを実行して",
            "画像生成ツールのバグを修正して",
            "ポートレート表示のHTMLコードを作成して",
        ]
        for text in false_cases:
            is_img, _, _ = is_image_creation_intent(text)
            self.assertFalse(is_img, f"Should be False: {text}")

        is_img, subcmd, _ = is_image_creation_intent("カフェにいる可愛い女の子の実写写真を作って")
        self.assertTrue(is_img)
        self.assertEqual(subcmd, "photo")

    def test_system_health_query_precision(self):
        # General narrative or coding questions must NOT trigger Termux telemetry injection
        self.assertFalse(_is_system_health_query("VIVANTの登場人物の心理状態について考察して"))
        self.assertFalse(_is_system_health_query("関数のメモリリークのバグを修正して"))
        self.assertFalse(_is_system_health_query("物語のステータス画面のUIを作成して"))

        # Actual device/system health queries MUST trigger
        self.assertTrue(_is_system_health_query("今のバッテリー残量は？"))
        self.assertTrue(_is_system_health_query("Termuxのシステム状態とメモリ使用量を教えて"))
        self.assertTrue(_is_system_health_query("端末の空き容量とヘルスチェックを実行して"))
        self.assertTrue(_is_system_health_query("今の状態は？"))

    def test_html_unique_dom_ids(self):
        html_path = ROOT_DIR / "interfaces/web/templates/index.html"
        html_text = html_path.read_text(encoding="utf-8")
        ids = re.findall(r'\bid=["\']([^"\']+)["\']', html_text)
        dup_ids = {k: v for k, v in Counter(ids).items() if v > 1}
        self.assertEqual(dup_ids, {}, f"Duplicate HTML IDs found: {dup_ids}")
        self.assertIn("mdSelWrap", ids)
        self.assertIn("chatMdBadgeWrap", ids)

    def test_dead_files_removed(self):
        dead_paths = [
            ROOT_DIR / "dynamic_tools/tugumi_context_engine_2026.py",
            ROOT_DIR / "dynamic_tools/tugumi_context_optimizer.py",
            ROOT_DIR / "dynamic_tools/tugumi_context_optimizer_2026.py",
            ROOT_DIR / "dynamic_tools/tugumi_omni_context_engine.py",
            ROOT_DIR / "data/memory.db",
            ROOT_DIR / "data/test_tmp_sanitation.txt",
        ]
        for p in dead_paths:
            self.assertFalse(p.exists(), f"Dead file still exists: {p}")

    def test_token_cost_tracker_multi_model_pricing(self):
        from interfaces.cli.token_cost_tracker import TokenCostTracker

        tracker = TokenCostTracker()
        self.assertEqual(tracker.model_label, "Gemini 3.8 Flash")
        self.assertAlmostEqual(tracker.input_rate_per_1m, 0.075)

        tracker.set_model("gemini-4-argon")
        self.assertEqual(tracker.model_label, "Gemini 4 Argon")
        self.assertAlmostEqual(tracker.input_rate_per_1m, 1.250)
        self.assertAlmostEqual(tracker.output_rate_per_1m, 5.000)

        tracker.set_model("gemini-3.5-flash-lite")
        self.assertEqual(tracker.model_label, "Gemini 3.5 Flash-Lite")
        self.assertAlmostEqual(tracker.input_rate_per_1m, 0.0375)

    def test_cli_clear_and_reset_separation_and_skill_handler(self):
        cli_src = (ROOT_DIR / "interfaces/cli/main.py").read_text(encoding="utf-8")
        # Ensure /clear is no longer swallowed by /reset
        self.assertIn('if user_input == "/reset":', cli_src)
        self.assertIn('if user_input in ("/clear", "/new"):', cli_src)
        # Ensure new parity commands exist in CLI
        for cmd in ('"/session"', '"/compact"', '"/credits"', '"/voice"', '"/goal"'):
            self.assertIn(cmd, cli_src)

    def test_webui_slash_command_parity_and_typo_suggestion(self):
        from interfaces.web.web_server import execute_slash_command

        # /credits
        res_cred = execute_slash_command("/credits", mode="light", session_id="test_sess")
        self.assertIsNotNone(res_cred)
        self.assertTrue(res_cred.get("is_command"))
        self.assertIn("実測トークン＆利用料金", res_cred.get("reply", ""))

        # /voice
        res_voice = execute_slash_command("/voice", mode="light", session_id="test_sess")
        self.assertIsNotNone(res_voice)
        self.assertIn("Aoede", res_voice.get("reply", ""))

        # /reset
        res_reset = execute_slash_command("/reset", mode="light", session_id="test_sess")
        self.assertIsNotNone(res_reset)
        self.assertIn("リセット", res_reset.get("reply", ""))

        # Typo suggestion
        res_typo = execute_slash_command("/statu", mode="light", session_id="test_sess")
        self.assertIsNotNone(res_typo)
        self.assertIn("/status", res_typo.get("reply", ""))

    def test_webui_image_generate_and_frontend_fixes(self):
        web_src = (ROOT_DIR / "interfaces/web/web_server.py").read_text(encoding="utf-8")
        html_src = (ROOT_DIR / "interfaces/web/templates/index.html").read_text(encoding="utf-8")

        # api_image_generate must not pass unsupported seed=req.seed to ImageStudioEngine.generate
        self.assertNotIn("seed=req.seed", web_src)
        # api_get_media_file must support path parameters
        self.assertIn('@app.get("/api/media/file/{file_type}/{filename:path}")', web_src)
        # Command palette must pass boolean false to runToolPro
        self.assertIn("runToolPro(sc.path, false,", html_src)
        # Safe media blocks preservation in md(t)
        self.assertIn("SAFEHTML_", html_src)


if __name__ == "__main__":
    unittest.main()
