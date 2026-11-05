#!/usr/bin/env python3
"""
TUGUMI Vision UI Agent (Vision-to-Action SOTA Engine)
Android Termux (Linux aarch64) 上で画面キャプチャと Gemini Vision API を連動させ、
端末画面をマルチモーダル視覚認識して自律的にタップ・入力・キーボード切替・スクロール操作を実行する最先端エージェント。
"""

import json
import os
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

# TUGUMIv6 パス追加
sys.path.insert(0, '/data/data/com.termux/files/home/TUGUMIv6')
from core.gemini_client import GeminiClient


class VisionUIAgent:
    """Gemini Vision による Android 実機高速自律視覚操作エージェント"""
    def __init__(self, width: int = 1080, height: int = 2400):
        self.width = width
        self.height = height
        self.client = GeminiClient()
        self.tmp_screen = Path("/data/local/tmp/vscreen.png")

    def capture_screen(self) -> bool:
        """Shizuku/rish を介して高速スクリーンショットを取得（ダイレクト読み込み）"""
        try:
            cmd = "screencap -p /data/local/tmp/vscreen.png && chmod 666 /data/local/tmp/vscreen.png"
            subprocess.run(["rish", "-c", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return self.tmp_screen.exists() and self.tmp_screen.stat().st_size > 1000
        except Exception as e:
            print(f"[VisionUIAgent] スクリーンキャプチャ失敗: {e}", file=sys.stderr)
            return False

    @staticmethod
    def get_latest_screenshot_path() -> Optional[str]:
        """端末内のスクリーンショット保存先から最新の画像パスを自動特定"""
        import glob
        candidate_dirs = [
            "/storage/emulated/0/Pictures/Screenshots",
            "/storage/emulated/0/DCIM/Screenshots",
            "/sdcard/Pictures/Screenshots",
            "/sdcard/DCIM/Screenshots"
        ]
        files = []
        for d in candidate_dirs:
            if os.path.exists(d):
                files.extend(glob.glob(os.path.join(d, "*.png")) + glob.glob(os.path.join(d, "*.jpg")))
        if not files:
            return None
        return max(files, key=os.path.getmtime)

    def inspect_latest_screenshot(self, query: str = "") -> dict[str, Any]:
        """最新のスクリーンショットを自動探索してVision解析"""
        latest_path = self.get_latest_screenshot_path()
        if not latest_path:
            return {"error": "スクリーンショットが見つかりませんでした"}
        
        prompt = f"""あなたはAndroid端末のスクリーンショットを視覚解析するAIエージェントです。
画像ファイル: {os.path.basename(latest_path)}
ユーザーの着眼点: "{query or '画面の状況、表示されている内容、キーやUI要素の詳細'}"

画像を詳しく観察し、日本語で状況や要点を詳細に報告してください。
"""
        raw_res = self.client.analyze_image(latest_path, prompt=prompt)
        return {
            "image_path": latest_path,
            "filename": os.path.basename(latest_path),
            "analysis": raw_res
        }

    def inspect_screen(self, focus_query: str = "") -> dict[str, Any]:
        """現在の画面をキャプチャし、視覚的な要約とUI状態を詳細分析"""
        if not self.capture_screen():
            return {"error": "画面キャプチャに失敗しました"}

        prompt = f"""あなたはAndroidスマートフォンの画面を分析する最高峰のVision AIです。
解像度は {self.width}x{self.height} です。
添付されたスクリーンショットを精査し、以下の点を日本語のJSONで報告してください。
ユーザーの着眼点: "{focus_query or '画面全体のUI、表示中のアプリ、キーボード状態'}"

必ず以下のJSON形式のみを出力してください:
```json
{{
  "current_app": "現在アクティブと思われるアプリ名やコンテキスト",
  "screen_summary": "画面全体の状況の説明",
  "keyboard_visible": true | false,
  "keyboard_type": "日本語テンキー" | "QWERTY" | "なし" | "その他",
  "visible_buttons": ["画面上の主要なボタンや入力欄の名称と位置のリスト"],
  "recommended_next_action": "次に推奨される操作"
}}
```
"""
        raw_res = self.client.analyze_image(str(self.tmp_screen), prompt=prompt)
        return self._extract_json(raw_res)

    def decide_action(self, instruction: str) -> dict[str, Any]:
        """画面をGemini Visionで解析し、ユーザー目標に対する次の1手を決定"""
        prompt = f"""あなたはAndroid端末 (解像度: {self.width}x{self.height}) を操作する最高精度のVision AIエージェントです。
添付された現在の画面スクリーンショットを精査し、以下のユーザーゴールを達成するための【次の1手】を決定してください。

【獲得済みキーボード知識（拓磨様直伝）】:
- 日本語テンキー（Gboard）の左下隅 [X: 108, Y: 2125] に「あa1」文字種切替キーが存在します。
  - 1回タップ: ひらがな ➔ アルファベット(a)
  - 2回タップ: ➔ 数字・記号(1)
  - 英数字を入力する前にキーボードが「あ」モードの場合は、action: "switch_keyboard_mode" を選択してください。

【ユーザーの目標/指示】:
"{instruction}"

【出力フォーマット】:
必ず以下の有効なJSONのみを出力してください（Markdownコードブロック ```json ... ``` 内に記述）:
```json
{{
  "thought": "画面の現在の状態の認識と、なぜこの操作を選択したかの詳細な推論",
  "action": "tap" | "type" | "switch_keyboard_mode" | "scroll_down" | "scroll_up" | "back" | "wait" | "done",
  "target_name": "操作対象のUI要素名（例: 検索欄, ログインボタン, 文字種切替）",
  "coordinate": [x, y], // tapまたはtypeの場合の画面絶対座標 [0〜{self.width}, 0〜{self.height}]
  "text": "入力する文字列（actionがtypeの場合のみ）",
  "is_goal_reached": true | false
}}
```
"""
        raw_res = self.client.analyze_image(str(self.tmp_screen), prompt=prompt)
        return self._extract_json(raw_res)

    def execute_action(self, decision: dict[str, Any]) -> bool:
        """決定されたアクションを実機で実行"""
        action = decision.get("action")
        coord = decision.get("coordinate")
        text = decision.get("text", "")

        if action == "tap" and coord:
            x, y = coord
            cmd = f"input tap {x} {y}"
            subprocess.run(["rish", "-c", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True

        elif action == "switch_keyboard_mode":
            # 拓磨様直伝: [108, 2125] の「あa1」キーをタップ
            subprocess.run(["rish", "-c", "input tap 108 2125"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            time.sleep(0.3)
            return True

        elif action == "type":
            if coord:
                x, y = coord
                subprocess.run(["rish", "-c", f"input tap {x} {y}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                time.sleep(0.3)
            # クリップボード経由の超高速ペースト (PASTE keyevent: 279)
            if text:
                try:
                    subprocess.run(["termux-clipboard-set", text], check=True)
                    time.sleep(0.1)
                    subprocess.run(["rish", "-c", "input keyevent 279"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
                except Exception:
                    safe_text = text.replace(" ", "%s")
                    subprocess.run(["rish", "-c", f"input text '{safe_text}'"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True

        elif action == "scroll_down":
            cmd = f"input swipe {self.width // 2} {int(self.height * 0.7)} {self.width // 2} {int(self.height * 0.3)} 300"
            subprocess.run(["rish", "-c", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True

        elif action == "scroll_up":
            cmd = f"input swipe {self.width // 2} {int(self.height * 0.3)} {self.width // 2} {int(self.height * 0.7)} 300"
            subprocess.run(["rish", "-c", cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True

        elif action == "back":
            subprocess.run(["rish", "-c", "input keyevent 4"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True

        elif action in ["wait", "done"]:
            return True

        return False

    def step(self, instruction: str) -> dict[str, Any]:
        """キャプチャ ➔ 視覚推論 ➔ 実機実行 の1ステップサイクル"""
        if not self.capture_screen():
            return {"error": "キャプチャ失敗", "action": "wait", "is_goal_reached": False}
        
        decision = self.decide_action(instruction)
        if decision.get("action") not in ["done", "wait"]:
            self.execute_action(decision)
            
        return decision

    def run_loop(self, goal: str, max_steps: int = 5) -> list[dict[str, Any]]:
        """ゴール達成まで最大 max_steps 回、自律ループを実行"""
        history = []
        for step_idx in range(1, max_steps + 1):
            res = self.step(goal)
            history.append({"step": step_idx, "result": res})
            if res.get("is_goal_reached") or res.get("action") == "done":
                break
            time.sleep(1.0)
        return history

    def _extract_json(self, raw_res: str) -> dict[str, Any]:
        """Markdown から JSON を頑健に抽出"""
        try:
            if "```json" in raw_res:
                json_str = raw_res.split("```json")[1].split("```")[0].strip()
            elif "```" in raw_res:
                json_str = raw_res.split("```")[1].split("```")[0].strip()
            else:
                json_str = raw_res.strip()
            return json.loads(json_str)
        except Exception as e:
            return {
                "thought": f"JSON解析エラー: {e}\n生出力: {raw_res}",
                "action": "wait",
                "coordinate": None,
                "is_goal_reached": False
            }

if __name__ == "__main__":
    agent = VisionUIAgent()
    target_goal = sys.argv[1] if len(sys.argv) > 1 else "現在の画面を観察し、状況を報告する"
    res = agent.step(target_goal)
    print("\n✅ ステップ完了:")
    print(json.dumps(res, ensure_ascii=False, indent=2))
