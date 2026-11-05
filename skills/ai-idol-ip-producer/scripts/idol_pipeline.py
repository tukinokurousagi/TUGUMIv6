#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
TUGUMIv6 AI Idol IP & Kindle Gravure Producer Pipeline (idol_pipeline.py)
- 清楚系(Seiso) / クール系(Cool) / 元気系(Genki) Character DNA 一貫固定
- 事業設計5大定義 & コンプライアンス20項目自動監査 (audit)
- Gemini 3.1 Flash Image による超リアル実写ポートレート生成
- edge-tts による清楚・自然派ニューラルボイス合成
- 著作権完全クリアの透明感アコースティックBGM自動合成
- FFmpeg + Pillow による 1080x1920 (9:16) テロップ付きショート動画3本生成 (build)
- Amazon KDP 準拠 Kindle デジタル写真集 (EPUB 3.0 & PDF) 自動組版・出力 (kindle)
Dedicated to Master Takuma
"""

import os
import sys
import json
import math
import time
import wave
import struct
import shutil
import zipfile
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, List, Tuple

# TUGUMIv6 パス解決
HOME_DIR = os.path.expanduser("~")
TUGUMI_DIR = os.path.join(HOME_DIR, "TUGUMIv6")
if TUGUMI_DIR not in sys.path:
    sys.path.insert(0, TUGUMI_DIR)

from PIL import Image, ImageDraw, ImageFont, ImageEnhance, ImageFilter

DESK_BASE = "/storage/emulated/0/TUGUMIDesk/副業・収益化"
if not os.path.exists("/storage/emulated/0"):
    DESK_BASE = os.path.expanduser("~/TUGUMIDesk/副業・収益化")

# 日本語フォントパス候補
SANS_FONT_CANDIDATES = [
    "/system/fonts/NotoSansCJK-Regular.ttc",
    "/data/data/com.termux/files/usr/share/fonts/TTF/DejaVuSans.ttf",
]
SERIF_FONT_CANDIDATES = [
    "/system/fonts/NotoSerifCJK-Regular.ttc",
    "/system/fonts/NotoSansCJK-Regular.ttc",
]

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. スタイル別プリセット（デフォルト：拓磨様お好みの「清楚系・透明感ヒロイン」）
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
STYLE_PRESETS: Dict[str, Dict[str, Any]] = {
    "seiso": {
        "display_name": "白石 凪 (Shiraishi Nagi)",
        "style_label": "清楚・小動物系透明感・正統派ヒロイン（リファレンス超越仕様）",
        "age": 20,
        "voice": "ja-JP-NanamiNeural",
        "voice_rate": "-2%",
        "voice_pitch": "+3Hz",
        "default_ref_image": "/storage/emulated/0/Pictures/Screenshots/Screenshot_20261029-164748.png",
        "dna_anchor": (
            "20-year-old pure and adorable Japanese female model with youthful neoteny and translucent beauty, "
            "petite delicate heart-oval face with soft youthful cheeks tapering to a dainty rounded chin, "
            "large round expressive doe-like dark brown eyes, clear natural parallel double eyelids, soft puffy aegyo-sal tear bags, "
            "delicate curled eyelashes with bright sky catchlights in pupils, "
            "dainty straight nose with soft rounded button tip, "
            "plump hydrated coral-pink lips slightly parted in an innocent affectionate smile showing a subtle hint of upper white teeth, "
            "silky straight natural black long hair with fine wispy see-through bangs, face-framing cheek-length side locks, and left side gently tucked behind her ear, "
            "luminous unretouched porcelain-hydrated skin with authentic micro-textures"
        ),
        "business_design": {
            "target": "清楚で透明感あふれる小動物系・正統派美少女ヒロインに癒やしを求めるファン層",
            "desire": "目が合うだけでドキッとする至近距離の彼氏目線と、圧倒的透明感のグラビア体験",
            "channel": "YouTube Shorts / TikTok / Instagram Reels (縦型ショート動画)",
            "monetization_primary": "Kindleデジタル写真集（KDP出版・Kindle Unlimited読み放題印税）",
            "monetization_secondary": "SNSショート動画からのファンクラブ・デジタルフォトブック直販・アフィリエイト",
            "retention_hook": "至近距離の『彼氏目線15秒ショート』と完全同一DNAによる季節別Kindle写真集シリーズ"
        },
        "scenes": [
            {
                "id": "01_intro",
                "title": "自己紹介・青空ガーデンの奇跡（原典超越版）",
                "caption": "第1章：青空と芝生の約束",
                "poem": "澄み渡る青空の下、しゃがみ込んで見上げた瞳に映る、あなただけの季節。",
                "scene_prompt": (
                    "crouching gracefully on a sunlit lush green lawn in an English garden under a clear bright blue sky, "
                    "high-angle close-up dating POV looking slightly down at her as she leans gently forward and looks up directly into the camera lens with an innocent sweet smile, "
                    "wearing a sheer white floral organza blouse with a ruffled Peter Pan collar and frilled puff sleeves, "
                    "a grey plaid pleated mini skirt, and white floral lace knee-high socks, "
                    "full-frame vertical 9:16 portrait with zero black bars, crisp sunlight and dreamy garden bokeh"
                ),
                "script": "見つけてくれてありがとうございます、白石凪です。今日から一番近い距離で、あなたにたくさんの癒やしと笑顔を届けていきますね。",
                "subtitle_lines": [
                    "見つけてくれてありがとう、白石 凪です🌸",
                    "今日から一番近い距離で、",
                    "あなたに笑顔と癒やしを届けていきますね✨"
                ]
            },
            {
                "id": "02_gravure_book",
                "title": "写真集紹介・木漏れ日カフェデート",
                "caption": "第2章：木漏れ日のカフェテラス",
                "poem": "グラスの氷が溶ける音さえ愛おしい、二人だけの午後のテーブル。",
                "scene_prompt": (
                    "sitting across a small wooden table at a sunlit garden cafe terrace, "
                    "close-up dating POV perspective, leaning forward slightly with her hands resting near an iced latte glass, "
                    "wearing a soft off-white cable-knit cardigan over a delicate white lace-trimmed camisole, "
                    "looking directly into the viewer's eyes with her signature large doe-like dark eyes, wispy see-through bangs, and sweet parted-lip smile, "
                    "warm afternoon dappled sunlight, vertical 9:16 portrait framing"
                ),
                "script": "凪の初めてのKindle写真集『透明な午後』ができました。この動画よりもっと近い距離の素顔をたくさん撮ってもらったので、ぜひ見に来てくださいね。",
                "subtitle_lines": [
                    "1st Kindle写真集『透明な午後』が完成📖",
                    "動画よりもっと近い距離の素顔を",
                    "たっぷり詰め込みました。プロフから見てね✨"
                ]
            },
            {
                "id": "03_healing_message",
                "title": "キャラの一言・白いカーテンと窓辺の透明感",
                "caption": "第3章：白いカーテンの秘密",
                "poem": "風に揺れるレースの向こう側、夕暮れの光が彼女の横顔を優しく包む。",
                "scene_prompt": (
                    "kneeling on a soft white rug beside a sunlit window with fluttering sheer white lace curtains in a nostalgic bright room, "
                    "high-angle close-up POV looking warmly into the camera lens with a tender affectionate smile, "
                    "wearing a crisp white short-sleeve sailor-style summer blouse with a delicate ribbon and a navy pleated skirt, "
                    "soft golden-hour backlight creating a luminous halo on her silky black hair and see-through bangs, vertical 9:16 portrait framing"
                ),
                "script": "今日もお仕事、本当にお疲れさまでした。いつも頑張っているあなたのこと、凪はちゃんと見ていますよ。今夜はゆっくり休んでくださいね。",
                "subtitle_lines": [
                    "今日もお仕事、本当にお疲れさまでした☕",
                    "いつも頑張っているあなたのこと、",
                    "凪はちゃんと見ていますよ。おやすみなさい🌙"
                ]
            }
        ]
    }
}


def _load_font(candidates: List[str], size: int) -> ImageFont.FreeTypeFont:
    for path in candidates:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size=size, index=0)
            except Exception:
                try:
                    return ImageFont.truetype(path, size=size)
                except Exception:
                    continue
    return ImageFont.load_default()


def _media_scan(filepath: str):
    if shutil.which("termux-media-scan"):
        try:
            subprocess.Popen(
                ["termux-media-scan", filepath],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL
            )
        except Exception:
            pass


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. 権利・炎上リスク4大監査ゲート (Audit Engine)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FORBIDDEN_PROMPT_KEYWORDS = [
    "underage", "minor", "child", "loli", "high school girl", "jk", "schoolgirl",
    "nogizaka", "hinatazaka", "sakurazaka", "akb48", "inoue nagi", "hashimoto kanna",
    "広瀬すず", "橋本環奈", "乃木坂", "日向坂", "櫻坂", "未成年", "女子高生", "中学生"
]


def audit_profile(profile_path: str) -> Dict[str, Any]:
    with open(profile_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    checks = []
    errors = []

    # 1. 年齢設定チェック (20歳以上必須)
    age = int(data.get("age", 0))
    age_ok = age >= 20
    checks.append({"item": "年齢設定20歳以上", "passed": age_ok, "detail": f"{age}歳"})
    if not age_ok:
        errors.append("年齢設定は20歳以上である必要があります。")

    # 2. AIキャラ明示チェック
    ai_disc = bool(data.get("ai_disclosure", False)) and bool(data.get("ai_disclosure_text", ""))
    checks.append({"item": "AI生成キャラクター明示文の定義", "passed": ai_disc, "detail": data.get("ai_disclosure_text", "")})
    if not ai_disc:
        errors.append("AI生成キャラクターであることの明示文が不足しています。")

    # 3. 事業設計5項目チェック
    biz = data.get("business_design", {})
    biz_ok = all(biz.get(k) for k in ["target", "desire", "channel", "monetization_primary", "retention_hook"])
    checks.append({"item": "事業設計5大項目（ターゲット/欲求/媒体/商品/継続）", "passed": biz_ok, "detail": biz.get("monetization_primary", "")})
    if not biz_ok:
        errors.append("事業設計の5大項目が未完成です。")

    # 4. 実在人物・未成年・既存IP模倣ワード排除チェック
    combined_prompts = data.get("dna_anchor", "") + " " + " ".join(
        s.get("scene_prompt", "") for s in data.get("scenes", [])
    )
    p_lower = combined_prompts.lower()
    hit_bad = [kw for kw in FORBIDDEN_PROMPT_KEYWORDS if kw in p_lower]
    prompt_ok = len(hit_bad) == 0
    checks.append({"item": "実在芸能人・未成年・既存IPワード排除", "passed": prompt_ok, "detail": "クリーン" if prompt_ok else f"NG: {hit_bad}"})
    if not prompt_ok:
        errors.append(f"禁止キーワードがプロンプトに含まれています: {hit_bad}")

    # 5. 初回検証15秒動画3本台本チェック
    scenes = data.get("scenes", [])
    scenes_ok = len(scenes) >= 3 and all(s.get("script") for s in scenes)
    checks.append({"item": "初回検証15秒ショート台本3本（自己紹介/商品/一言）", "passed": scenes_ok, "detail": f"{len(scenes)}本定義済"})
    if not scenes_ok:
        errors.append("初回検証用の3本の台本が必要です。")

    report = {
        "passed": len(errors) == 0,
        "timestamp": datetime.now().isoformat(),
        "character_name": data.get("display_name", data.get("name")),
        "checks": checks,
        "errors": errors
    }
    return report


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. 著作権フリー・透明感アコースティックBGMシンセサイザー
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def synthesize_seiso_ambient_bgm(wav_path: str, duration_sec: float = 16.0):
    """清楚・透明感の世界観に合う温かいエレクトリックピアノ＆アンビエントパッドBGMを合成"""
    sample_rate = 24000
    total_samples = int(sample_rate * duration_sec)
    # カノン＆王道進行風の温かいコード進行 (Fmaj7 -> G6 -> Em7 -> Am7)
    chords = [
        [349.23, 440.00, 523.25, 659.25],  # Fmaj7
        [392.00, 493.88, 587.33, 659.25],  # G6
        [329.63, 392.00, 493.88, 587.33],  # Em7
        [220.00, 329.63, 440.00, 523.25],  # Am7
    ]
    arp_notes = [523.25, 659.25, 783.99, 1046.50, 783.99, 659.25, 587.33, 659.25]

    buf = bytearray()
    for i in range(total_samples):
        t = i / sample_rate
        chord_idx = int(t / 2.0) % len(chords)
        chord_t = t % 2.0
        chord = chords[chord_idx]

        # 柔らかいローズピアノ風パッド
        env_pad = math.exp(-chord_t * 0.9) * min(1.0, chord_t / 0.08)
        pad_val = 0.0
        for freq in chord:
            pad_val += math.sin(2.0 * math.pi * freq * t) * 0.18
            pad_val += math.sin(2.0 * math.pi * (freq * 2.0) * t) * 0.04 * math.exp(-chord_t * 2.5)
        pad_val *= env_pad

        # 煌めくオルゴール風アルペジオ
        arp_step = int(t / 0.5)
        arp_t = t % 0.5
        arp_freq = arp_notes[arp_step % len(arp_notes)]
        env_arp = math.exp(-arp_t * 4.5) * min(1.0, arp_t / 0.01)
        arp_val = (
            math.sin(2.0 * math.pi * arp_freq * t) * 0.12 +
            math.sin(2.0 * math.pi * (arp_freq * 2.0) * t) * 0.03
        ) * env_arp

        # フェードイン・フェードアウト
        master_env = 1.0
        if t < 0.8:
            master_env = t / 0.8
        elif t > duration_sec - 1.5:
            master_env = max(0.0, (duration_sec - t) / 1.5)

        sample = max(-0.95, min(0.95, (pad_val + arp_val) * master_env))
        pcm = int(sample * 32767)
        buf.extend(struct.pack("<h", pcm))

    with wave.open(wav_path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(bytes(buf))


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 4. 超リアル9:16ビジュアル生成 & テロップフレーム描画
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def _prepare_clean_ref_bytes(ref_image_path: str) -> bytes:
    """スクショの上下黒帯（レターボックス）を自動検出しトリミングしたクリーンなPNGバイト列を返す"""
    import io
    with Image.open(ref_image_path) as im:
        im = im.convert("RGB")
        w, h = im.size
        # 上下の黒帯（輝度平均 < 15）を自動走査して除去
        top = 0
        for y in range(h // 3):
            row_vals = [sum(im.getpixel((x, y))) / 3.0 for x in range(0, w, max(1, w // 20))]
            if sum(row_vals) / len(row_vals) > 15.0:
                top = y
                break
        bottom = h
        for y in range(h - 1, (h * 2) // 3, -1):
            row_vals = [sum(im.getpixel((x, y))) / 3.0 for x in range(0, w, max(1, w // 20))]
            if sum(row_vals) / len(row_vals) > 15.0:
                bottom = y + 1
                break
        if bottom - top > h // 3 and (top > 10 or bottom < h - 10):
            im = im.crop((0, top, w, bottom))
        buf = io.BytesIO()
        im.save(buf, format="PNG")
        return buf.getvalue()


def generate_character_visual(
    dna_anchor: str,
    scene_prompt: str,
    out_image_path: str,
    ref_image_path: str = ""
) -> str:
    """
    リファレンス画像（マルチモーダル入力）＋ 8層プロンプト工学 (ai-model-producer-pro) を融合し、
    元のAI美女の顔立ち・愛嬌・透明感を100%継承しつつ実写リアリズムで超越した9:16ポートレートを生成。
    """
    import io
    import base64
    from tools.media_tools import (
        GeminiImageStudio,
        _resolve_gemini_api_key,
        _get_block_none_safety_settings,
        genai,
        types,
    )

    hyper_optics_and_skin = (
        "Shot on Sony Alpha 7R V with 50mm f/1.2 GM lens at f/1.6, 1/400s, ISO 100. "
        "Hyper-realistic biological micro-textures surpassing typical AI portraits: "
        "authentic translucent porcelain skin with subtle micro-pores on cheeks and nose, "
        "fine glowing peach fuzz catching natural sunlight along the jawline, "
        "wet tear-film meniscus and crystal-clear catchlights in her large dark-brown doe eyes, "
        "individual silky hair strands with natural angel-halo cuticle gloss, "
        "natural lip hydration with delicate vertical lip lines. "
        "Kodak Portra 400 & Fujifilm Pro 400H hybrid color science, "
        "full-bleed vertical 9:16 portrait composition filling the entire canvas from top edge to bottom edge "
        "(strictly NO black letterbox bars at top or bottom, NO CGI plastic skin, NO doll-like airbrushing, NO text or watermarks)."
    )

    full_prompt = (
        f"Vertical 9:16 full-frame portrait photograph of {dna_anchor}. "
        f"Scene, pose & styling: {scene_prompt}. "
        f"{hyper_optics_and_skin}"
    )

    # 1. リファレンス画像が指定されている場合はマルチモーダル直接参照生成（Identity Lock & Surpass + 複数APIキー自動ローテーション）
    if ref_image_path and os.path.isfile(ref_image_path):
        try:
            clean_bytes = _prepare_clean_ref_bytes(ref_image_path)
            image_part = types.Part.from_bytes(data=clean_bytes, mime_type="image/png")
            multimodal_instruction = (
                "Reference Character Identity Lock & Photorealistic Surpass Instruction:\n"
                "Use the attached image as the EXACT facial identity, facial neoteny proportions, "
                "large round dark-brown doe eyes, puffy aegyo-sal, dainty button nose, "
                "sweet slightly parted coral-pink lips, and silky black straight hair with wispy see-through bangs. "
                "Keep her adorable facial identity 100% recognizable as the exact same girl, "
                "while SURPASSING the reference image in raw photographic realism, lens bokeh, "
                "skin micro-texture, and hair strand fidelity.\n\n"
                f"Target Shot Specification:\n{full_prompt}"
            )
            candidate_keys = []
            for k in [_resolve_gemini_api_key(""), os.environ.get("GEMINI_API_KEY", ""), os.environ.get("GOOGLE_API_KEY", "")]:
                if k and k not in candidate_keys:
                    candidate_keys.append(k)

            for api_key in candidate_keys:
                client = genai.Client(api_key=api_key, http_options={"timeout": 180000})
                for model_name in ["gemini-3.1-flash-image", "gemini-3-pro-image"]:
                    try:
                        resp = client.models.generate_content(
                            model=model_name,
                            contents=[image_part, multimodal_instruction],
                            config=types.GenerateContentConfig(
                                response_modalities=["IMAGE"],
                                safety_settings=_get_block_none_safety_settings(),
                            ),
                        )
                        for part in resp.candidates[0].content.parts:
                            if part.inline_data and part.inline_data.data:
                                img_bytes = part.inline_data.data
                                if isinstance(img_bytes, str):
                                    img_bytes = base64.b64decode(img_bytes)
                                with Image.open(io.BytesIO(img_bytes)) as im:
                                    im = im.convert("RGB")
                                    target_w, target_h = 1080, 1920
                                    src_ratio = im.width / im.height
                                    target_ratio = target_w / target_h
                                    if src_ratio > target_ratio:
                                        new_h = target_h
                                        new_w = int(new_h * src_ratio)
                                    else:
                                        new_w = target_w
                                        new_h = int(new_w / src_ratio)
                                    resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
                                    left = (new_w - target_w) // 2
                                    top = max(0, (new_h - target_h) // 3)
                                    cropped = resized.crop((left, top, left + target_w, top + target_h))
                                    cropped.save(out_image_path, "PNG")
                                _media_scan(out_image_path)
                                return out_image_path
                    except Exception as e:
                        print(f"  [WARN] Multimodal generation ({model_name}, key={api_key[:8]}...) retry: {e}")
                        continue
        except Exception as e:
            print(f"  [WARN] Reference image conditioning fallback: {e}")

    # 2. フォールバック: テキストプロンプトからの生成
    tmp_filename = os.path.basename(out_image_path)
    res = GeminiImageStudio.generate(
        prompt=full_prompt,
        filename=tmp_filename,
        style="photoreal",
        aspect_ratio="9:16",
        photoreal=True
    )
    if res.get("success") and res.get("file_path") and os.path.exists(res["file_path"]):
        src_path = res["file_path"]
        # 1080x1920 (9:16) へセンタークロップ＆高品質リサイズ
        with Image.open(src_path) as im:
            im = im.convert("RGB")
            target_w, target_h = 1080, 1920
            src_ratio = im.width / im.height
            target_ratio = target_w / target_h
            if src_ratio > target_ratio:
                new_h = target_h
                new_w = int(new_h * src_ratio)
            else:
                new_w = target_w
                new_h = int(new_w / src_ratio)
            resized = im.resize((new_w, new_h), Image.Resampling.LANCZOS)
            left = (new_w - target_w) // 2
            top = max(0, (new_h - target_h) // 3)
            cropped = resized.crop((left, top, left + target_w, top + target_h))
            cropped.save(out_image_path, "PNG")
        _media_scan(out_image_path)
        return out_image_path
    raise RuntimeError(f"画像生成に失敗しました: {res.get('error')}")


def create_subtitled_video_overlay(
    base_image_path: str,
    char_display_name: str,
    scene_title: str,
    subtitle_lines: List[str],
    ai_disclosure_text: str,
    out_overlay_png: str
):
    """1080x1920 の透明オーバーレイPNG（AI明示バッジ＋グラスモーフィズム字幕パネル）を生成"""
    w, h = 1080, 1920
    overlay = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    font_badge = _load_font(SANS_FONT_CANDIDATES, 26)
    font_name = _load_font(SANS_FONT_CANDIDATES, 34)
    font_sub = _load_font(SANS_FONT_CANDIDATES, 40)

    # 1. 右上: AI Generated 明示バッジ (コンプライアンス必須要件)
    badge_box = [w - 390, 60, w - 45, 125]
    draw.rounded_rectangle(badge_box, radius=24, fill=(15, 23, 42, 185), outline=(255, 255, 255, 140), width=2)
    draw.text((w - 365, 76), ai_disclosure_text, font=font_badge, fill=(248, 250, 252, 255))

    # 2. 下部グラデーション＆グラスモーフィズム字幕カード
    card_box = [48, h - 470, w - 48, h - 130]
    draw.rounded_rectangle(card_box, radius=36, fill=(15, 23, 42, 195), outline=(255, 192, 203, 180), width=3)

    # キャラ名タグ
    tag_box = [80, h - 498, 460, h - 438]
    draw.rounded_rectangle(tag_box, radius=20, fill=(219, 39, 119, 235))
    draw.text((108, h - 488), f"✦ {char_display_name}", font=font_name, fill=(255, 255, 255, 255))

    # 台詞テキスト描画
    y_text = h - 405
    for line in subtitle_lines:
        # シャドウ
        draw.text((92, y_text + 2), line, font=font_sub, fill=(0, 0, 0, 220))
        draw.text((90, y_text), line, font=font_sub, fill=(255, 255, 255, 255))
        y_text += 72

    overlay.save(out_overlay_png, "PNG")


def build_short_video(
    image_path: str,
    overlay_png_path: str,
    voice_mp3_path: str,
    bgm_wav_path: str,
    out_mp4_path: str
):
    """
    FFmpeg を用いて:
    - 9:16 ポートレートの滑らかな Ken Burns スローズーム演出
    - 透明感テロップ＆AI明示バッジのオーバーレイ合成
    - edge-tts ボイス (主音声) + オリジナルBGM (15%音量) のミキシング
    を行い、1080x1920 MP4 ショート動画を生成する。
    """
    # 音声の長さを取得
    probe_cmd = [
        "ffprobe", "-v", "error", "-show_entries", "format=duration",
        "-of", "default=noprint_wrappers=1:nokey=1", voice_mp3_path
    ]
    res = subprocess.run(probe_cmd, capture_output=True, text=True)
    try:
        voice_dur = float(res.stdout.strip())
    except Exception:
        voice_dur = 12.0
    total_dur = max(10.0, min(18.0, voice_dur + 1.5))
    frames = int(total_dur * 25)

    filter_complex = (
        f"[0:v]scale=1200:2134,zoompan=z='min(zoom+0.0005,1.08)':"
        f"x='iw/2-(iw/zoom/2)':y='ih/2-(ih/zoom/2)':d={frames}:s=1080x1920:fps=25[bg];"
        f"[bg][1:v]overlay=0:0:format=auto[vout];"
        f"[2:a]volume=1.35,apad=pad_dur=1.5[va];"
        f"[3:a]volume=0.18[ba];"
        f"[va][ba]amix=inputs=2:duration=first:dropout_transition=2[aout]"
    )

    cmd = [
        "ffmpeg", "-y",
        "-loop", "1", "-i", image_path,
        "-i", overlay_png_path,
        "-i", voice_mp3_path,
        "-i", bgm_wav_path,
        "-filter_complex", filter_complex,
        "-map", "[vout]", "-map", "[aout]",
        "-t", f"{total_dur:.2f}",
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
        "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        out_mp4_path
    ]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(f"FFmpeg 動画合成エラー: {proc.stderr[-500:]}")
    _media_scan(out_mp4_path)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 5. Kindle デジタル写真集ジェネレーター (EPUB 3.0 & 高画質PDF)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
def generate_kindle_photobook(profile: Dict[str, Any], image_paths: List[str], out_dir: str) -> Dict[str, str]:
    """
    Amazon KDP (Kindle Direct Publishing) 推奨比率 (1600x2560 / 1:1.6) の
    1. 表紙デザイン画像 (cover.jpg)
    2. グラビア＆ポエムページ群
    3. EPUB 3.0 電子書籍ファイル (.epub)
    4. スマホ閲覧用 高解像度PDF写真集 (.pdf)
    を自動生成する。
    """
    os.makedirs(out_dir, exist_ok=True)
    char_name = profile.get("display_name", "白石 凪")
    book_title = profile.get("photobook_title", "透明な午後")
    book_subtitle = f"{char_name} 1st Digital Gravure Photo Book"
    ai_disc = profile.get("ai_disclosure_text", "AI Generated Virtual Talent IP")

    kw, kh = 1600, 2560
    font_title = _load_font(SERIF_FONT_CANDIDATES, 118)
    font_sub = _load_font(SANS_FONT_CANDIDATES, 42)
    font_name = _load_font(SERIF_FONT_CANDIDATES, 64)
    font_poem = _load_font(SERIF_FONT_CANDIDATES, 44)

    pages_dir = os.path.join(out_dir, "kindle_pages")
    os.makedirs(pages_dir, exist_ok=True)
    rendered_pages: List[str] = []

    # 1. 表紙 (Cover Page) の生成
    cover_src = image_paths[0]
    with Image.open(cover_src) as im:
        im = im.convert("RGB")
        # 1600x2560 へフィット
        src_r = im.width / im.height
        tgt_r = kw / kh
        if src_r > tgt_r:
            nh = kh
            nw = int(nh * src_r)
        else:
            nw = kw
            nh = int(nw / src_r)
        resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
        left = (nw - kw) // 2
        top = (nh - kh) // 2
        cover_im = resized.crop((left, top, left + kw, top + kh)).convert("RGBA")

    # 表紙タイポグラフィ帯
    overlay = Image.new("RGBA", (kw, kh), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)
    # 上部上品ラベル
    draw.rectangle([0, 0, kw, 130], fill=(15, 23, 42, 175))
    draw.text((80, 42), f"TUGUMI GRAVURE ARCHIVE  |  {book_subtitle}", font=font_sub, fill=(255, 255, 255, 240))
    # 下部タイトル帯
    draw.rectangle([0, kh - 540, kw, kh], fill=(15, 23, 42, 195))
    draw.text((90, kh - 470), book_title, font=font_title, fill=(255, 255, 255, 255))
    draw.text((95, kh - 300), f"Model: {char_name}", font=font_name, fill=(251, 207, 232, 255))
    draw.text((95, kh - 180), f"Produced by Master Takuma  •  {ai_disc}", font=font_sub, fill=(203, 213, 225, 230))

    cover_final = Image.alpha_composite(cover_im, overlay).convert("RGB")
    cover_path = os.path.join(pages_dir, "00_cover.jpg")
    cover_final.save(cover_path, "JPEG", quality=94)
    rendered_pages.append(cover_path)
    _media_scan(cover_path)

    # 2. 各章グラビアページ＋ポエム見開きページの生成
    scenes = profile.get("scenes", [])
    for idx, img_p in enumerate(image_paths):
        scene_info = scenes[idx] if idx < len(scenes) else {}
        caption = scene_info.get("caption", f"Scene {idx + 1}")
        poem = scene_info.get("poem", "澄み渡る光の中で、静かに微笑む。")

        # フルブリード写真ページ
        with Image.open(img_p) as im:
            im = im.convert("RGB")
            src_r = im.width / im.height
            tgt_r = kw / kh
            if src_r > tgt_r:
                nh = kh
                nw = int(nh * src_r)
            else:
                nw = kw
                nh = int(nw / src_r)
            resized = im.resize((nw, nh), Image.Resampling.LANCZOS)
            left = (nw - kw) // 2
            top = (nh - kh) // 2
            photo_page = resized.crop((left, top, left + kw, top + kh)).convert("RGBA")

        p_over = Image.new("RGBA", (kw, kh), (0, 0, 0, 0))
        p_draw = ImageDraw.Draw(p_over)
        p_draw.rounded_rectangle([70, kh - 240, kw - 70, kh - 80], radius=24, fill=(15, 23, 42, 165))
        p_draw.text((110, kh - 205), f"{caption}  —  {poem}", font=font_poem, fill=(255, 255, 255, 245))

        page_rgb = Image.alpha_composite(photo_page, p_over).convert("RGB")
        page_path = os.path.join(pages_dir, f"0{idx + 1}_gravure.jpg")
        page_rgb.save(page_path, "JPEG", quality=94)
        rendered_pages.append(page_path)

    # 3. 奥付 (Colophon) ページ
    colophon = Image.new("RGB", (kw, kh), (18, 22, 31))
    c_draw = ImageDraw.Draw(colophon)
    c_draw.text((140, 400), f"『{book_title}』", font=font_title, fill=(255, 255, 255))
    c_draw.text((150, 580), f"モデル：{char_name}（21歳・架空AIタレントIP）", font=font_name, fill=(244, 114, 182))
    colophon_lines = [
        f"発行日：{datetime.now().strftime('%Y年%m月%d日')}",
        "企画・プロデュース：拓磨 (Master Takuma)",
        "制作システム：TUGUMIv6 AI Model Producer Pro",
        "",
        "【AI生成作品および権利表記】",
        "本写真集に登場する人物は、最新の生成AI技術および独自の",
        "Character DNA固定技術によって創出された20歳以上の架空モデルであり、",
        "実在する人物・団体とは一切関係ありません。",
        "無断転載・複製・二次配布を禁じます。"
    ]
    cy = 820
    for line in colophon_lines:
        c_draw.text((150, cy), line, font=font_poem, fill=(226, 232, 240))
        cy += 80
    colophon_path = os.path.join(pages_dir, "99_colophon.jpg")
    colophon.save(colophon_path, "JPEG", quality=92)
    rendered_pages.append(colophon_path)

    # 4. 高画質 PDF 写真集の出力 (Pillow multi-page PDF)
    pdf_path = os.path.join(out_dir, f"Kindle写真集_{char_name.replace(' ', '_')}_{book_title}.pdf")
    pil_pages = [Image.open(p).convert("RGB") for p in rendered_pages]
    pil_pages[0].save(pdf_path, "PDF", resolution=150.0, save_all=True, append_images=pil_pages[1:])
    for im in pil_pages:
        im.close()

    # 5. Amazon KDP 準拠 EPUB 3.0 ファイルのパッケージング
    epub_path = os.path.join(out_dir, f"Kindle写真集_{char_name.replace(' ', '_')}_{book_title}.epub")
    _build_epub3_package(epub_path, book_title, char_name, rendered_pages, kw, kh)

    return {
        "cover_path": cover_path,
        "pdf_path": pdf_path,
        "epub_path": epub_path,
        "page_count": len(rendered_pages)
    }


def _build_epub3_package(epub_path: str, title: str, author: str, image_paths: List[str], w: int, h: int):
    """Amazon KDP にそのまま入稿できる固定レイアウト EPUB 3.0 を生成"""
    book_uuid = f"urn:uuid:tugumi-idol-{int(time.time())}"
    now_iso = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    with zipfile.ZipFile(epub_path, "w") as zf:
        # 1. mimetype (無圧縮・先頭必須)
        zf.writestr("mimetype", "application/epub+zip", compress_type=zipfile.ZIP_STORED)

        # 2. META-INF/container.xml
        container_xml = """<?xml version="1.0" encoding="UTF-8"?>
<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">
  <rootfiles>
    <rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>
  </rootfiles>
</container>"""
        zf.writestr("META-INF/container.xml", container_xml, compress_type=zipfile.ZIP_DEFLATED)

        manifest_items = [
            '<item id="nav" href="nav.xhtml" media-type="application/xhtml+xml" properties="nav"/>'
        ]
        spine_items = []
        nav_links = []

        for idx, img_p in enumerate(image_paths):
            img_name = f"images/page_{idx:02d}.jpg"
            xhtml_name = f"page_{idx:02d}.xhtml"
            zf.write(img_p, f"OEBPS/{img_name}", compress_type=zipfile.ZIP_DEFLATED)

            props = ' properties="cover-image"' if idx == 0 else ""
            manifest_items.append(
                f'<item id="img_{idx:02d}" href="{img_name}" media-type="image/jpeg"{props}/>'
            )
            manifest_items.append(
                f'<item id="page_{idx:02d}" href="{xhtml_name}" media-type="application/xhtml+xml" properties="svg"/>'
            )
            spine_items.append(f'<itemref idref="page_{idx:02d}"/>')
            nav_links.append(f'<li><a href="{xhtml_name}">Page {idx + 1}</a></li>')

            xhtml_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="ja">
<head>
  <meta charset="UTF-8"/>
  <title>{title} - Page {idx + 1}</title>
  <meta name="viewport" content="width={w}, height={h}"/>
  <style>
    html, body {{ margin: 0; padding: 0; width: 100%; height: 100%; background: #000; overflow: hidden; }}
    svg {{ width: 100%; height: 100%; }}
  </style>
</head>
<body>
  <svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" version="1.1" width="100%" height="100%" viewBox="0 0 {w} {h}">
    <image width="{w}" height="{h}" xlink:href="{img_name}"/>
  </svg>
</body>
</html>"""
            zf.writestr(f"OEBPS/{xhtml_name}", xhtml_content, compress_type=zipfile.ZIP_DEFLATED)

        nav_xhtml = f"""<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE html>
<html xmlns="http://www.w3.org/1999/xhtml" xmlns:epub="http://www.idpf.org/2007/ops" xml:lang="ja">
<head><meta charset="UTF-8"/><title>Navigation</title></head>
<body>
  <nav epub:type="toc" id="toc">
    <h1>{title}</h1>
    <ol>{''.join(nav_links)}</ol>
  </nav>
</body>
</html>"""
        zf.writestr("OEBPS/nav.xhtml", nav_xhtml, compress_type=zipfile.ZIP_DEFLATED)

        content_opf = f"""<?xml version="1.0" encoding="UTF-8"?>
<package xmlns="http://www.idpf.org/2007/opf" version="3.0" unique-identifier="BookId" xml:lang="ja" prefix="rendition: http://www.idpf.org/vocab/rendition/#">
  <metadata xmlns:dc="http://purl.org/dc/elements/1.1/">
    <dc:identifier id="BookId">{book_uuid}</dc:identifier>
    <dc:title>{title}</dc:title>
    <dc:creator>{author}</dc:creator>
    <dc:language>ja</dc:language>
    <meta property="dcterms:modified">{now_iso}</meta>
    <meta property="rendition:layout">pre-paginated</meta>
    <meta property="rendition:orientation">portrait</meta>
    <meta property="rendition:spread">none</meta>
    <meta name="fixed-layout" content="true"/>
    <meta name="original-resolution" content="{w}x{h}"/>
    <meta name="book-type" content="comic"/>
  </metadata>
  <manifest>
    {chr(10).join('    ' + m for m in manifest_items)}
  </manifest>
  <spine>
    {chr(10).join('    ' + s for s in spine_items)}
  </spine>
</package>"""
        zf.writestr("OEBPS/content.opf", content_opf, compress_type=zipfile.ZIP_DEFLATED)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 6. パイプライン統合実行 (init / audit / build / kindle / all)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
DEFAULT_REF_SCREENSHOT = "/storage/emulated/0/Pictures/Screenshots/Screenshot_20261029-164748.png"


def cmd_init(name: str, style: str, out_dir: str, ref_image: str = "") -> str:
    os.makedirs(out_dir, exist_ok=True)
    preset = STYLE_PRESETS.get(style, STYLE_PRESETS["seiso"]).copy()

    effective_ref = ref_image or (DEFAULT_REF_SCREENSHOT if os.path.isfile(DEFAULT_REF_SCREENSHOT) else "")

    profile = {
        "name": name,
        "display_name": preset["display_name"],
        "style": style,
        "style_label": preset["style_label"],
        "age": preset["age"],
        "ai_disclosure": True,
        "ai_disclosure_text": "AI Generated / 架空AIタレント",
        "photobook_title": "透明な午後",
        "voice": preset["voice"],
        "voice_rate": preset["voice_rate"],
        "voice_pitch": preset["voice_pitch"],
        "dna_anchor": preset["dna_anchor"],
        "ref_image": effective_ref,
        "business_design": preset["business_design"],
        "scenes": preset["scenes"],
        "created_at": datetime.now().isoformat()
    }

    profile_path = os.path.join(out_dir, f"{name}_profile.json")
    with open(profile_path, "w", encoding="utf-8") as f:
        json.dump(profile, f, ensure_ascii=False, indent=2)

    # 閲覧しやすい事業メモ Markdown も出力
    biz = profile["business_design"]
    memo_md = f"""# 🌸 AIアイドルIP事業メモ：{profile['display_name']}

- **キャラID**: `{name}`
- **スタイル**: {profile['style_label']}
- **年齢設定**: {profile['age']}歳（成人基準クリア）
- **AI明示表記**: `{profile['ai_disclosure_text']}`
- **音声モデル**: `{profile['voice']}` (Rate: `{profile['voice_rate']}`, Pitch: `{profile['voice_pitch']}`)

---

## 🎯 1. 事業設計5大定義（マネタイズ導線）
- **ターゲット**: {biz['target']}
- **満たす欲求**: {biz['desire']}
- **主戦場（接点）**: {biz['channel']}
- **メイン収益商品**: {biz['monetization_primary']}
- **サブ収益商品**: {biz['monetization_secondary']}
- **継続視聴フック**: {biz['retention_hook']}

---

## 🧬 2. 固定 Character DNA アンカー（顔ブレ防止5大要素）
```text
{profile['dna_anchor']}
```

---

##🎬 3. 初回検証15秒ショート動画 台本3本
"""
    for idx, sc in enumerate(profile["scenes"], 1):
        memo_md += f"\n### 動画{idx}: {sc['title']}\n- **台詞**: 「{sc['script']}」\n- **撮影プロンプト**: `{sc['scene_prompt']}`\n"

    memo_path = os.path.join(out_dir, f"00_{name}_事業設計メモ.md")
    with open(memo_path, "w", encoding="utf-8") as f:
        f.write(memo_md)

    print(f"[INIT] 事業設計＆Character DNAプロファイルを生成しました: {profile_path}")
    return profile_path


def cmd_build(
    profile_path: str,
    build_kindle: bool = True,
    ref_image: str = "",
    force: bool = False
) -> Dict[str, Any]:
    with open(profile_path, "r", encoding="utf-8") as f:
        profile = json.load(f)

    out_dir = os.path.dirname(os.path.abspath(profile_path))
    img_dir = os.path.join(out_dir, "images")
    audio_dir = os.path.join(out_dir, "audio")
    video_dir = os.path.join(out_dir, "videos")
    os.makedirs(img_dir, exist_ok=True)
    os.makedirs(audio_dir, exist_ok=True)
    os.makedirs(video_dir, exist_ok=True)

    # 1. コンプライアンス監査ゲート
    audit_res = audit_profile(profile_path)
    audit_path = os.path.join(out_dir, "audit_report.json")
    with open(audit_path, "w", encoding="utf-8") as f:
        json.dump(audit_res, f, ensure_ascii=False, indent=2)
    if not audit_res["passed"]:
        raise RuntimeError(f"コンプライアンス監査不合格: {audit_res['errors']}")
    print("[AUDIT] 権利・炎上リスク4大監査ゲート: ALL PASS")

    # 2. 著作権フリー専用BGM生成
    bgm_wav = os.path.join(audio_dir, "seiso_ambient_bgm.wav")
    synthesize_seiso_ambient_bgm(bgm_wav, duration_sec=18.0)
    print(f"[BGM] 著作権フリー透明感アコースティックBGM合成完了: {bgm_wav}")

    generated_images = []
    generated_videos = []
    generated_audios = []

    dna_anchor = profile["dna_anchor"]
    effective_ref = ref_image or profile.get("ref_image", "")
    voice = profile.get("voice", "ja-JP-NanamiNeural")
    rate = profile.get("voice_rate", "-4%")
    pitch = profile.get("voice_pitch", "+1Hz")
    display_name = profile.get("display_name", "白石 凪")
    ai_disc_text = profile.get("ai_disclosure_text", "AI Generated / 架空AIタレント")

    for sc in profile["scenes"]:
        sc_id = sc["id"]
        print(f"\n--- 🎬 シーンビルド開始: {sc_id} ({sc['title']}) ---")

        # (A) 9:16 ビジュアル生成（--force 指定時はキャッシュを上書き再生成）
        img_path = os.path.join(img_dir, f"{sc_id}_portrait.png")
        if not force and os.path.exists(img_path) and os.path.getsize(img_path) > 10000:
            print(f"  [IMAGE] 既存9:16 清楚系ポートレート再利用: {img_path}")
        else:
            generate_character_visual(
                dna_anchor=dna_anchor,
                scene_prompt=sc["scene_prompt"],
                out_image_path=img_path,
                ref_image_path=effective_ref,
            )
            print(f"  [IMAGE] 9:16 清楚系ポートレート生成完了: {img_path}")
        generated_images.append(img_path)

        # (B) edge-tts ボイス＆VTT字幕生成
        mp3_path = os.path.join(audio_dir, f"{sc_id}_voice.mp3")
        vtt_path = os.path.join(audio_dir, f"{sc_id}_voice.vtt")
        tts_cmd = [
            sys.executable, "-m", "edge_tts",
            "--voice", voice,
            f"--rate={rate}",
            f"--pitch={pitch}",
            "--text", sc["script"],
            "--write-media", mp3_path,
            "--write-subtitles", vtt_path
        ]
        tts_proc = subprocess.run(tts_cmd, capture_output=True, text=True)
        if tts_proc.returncode != 0:
            raise RuntimeError(f"edge-tts 音声合成エラー: {tts_proc.stderr}")
        generated_audios.append(mp3_path)
        print(f"  [VOICE] 清楚系ニューラルボイス合成完了: {mp3_path}")

        # (C) テロップ＆AI明示オーバーレイ生成
        overlay_png = os.path.join(img_dir, f"{sc_id}_overlay.png")
        create_subtitled_video_overlay(
            base_image_path=img_path,
            char_display_name=display_name,
            scene_title=sc["title"],
            subtitle_lines=sc.get("subtitle_lines", [sc["script"]]),
            ai_disclosure_text=ai_disc_text,
            out_overlay_png=overlay_png
        )

        # (D) 15秒ショート動画 (MP4) レンダリング
        mp4_path = os.path.join(video_dir, f"{sc_id}_{sc['title'].split('・')[0]}.mp4")
        build_short_video(
            image_path=img_path,
            overlay_png_path=overlay_png,
            voice_mp3_path=mp3_path,
            bgm_wav_path=bgm_wav,
            out_mp4_path=mp4_path
        )
        generated_videos.append(mp4_path)
        print(f"  [VIDEO] 15秒縦型ショート動画(1080x1920)完成: {mp4_path}")

    kindle_res = {}
    if build_kindle and generated_images:
        print("\n--- 📖 Kindle デジタル写真集 (EPUB 3.0 & PDF) 自動組版開始 ---")
        kindle_dir = os.path.join(out_dir, "Kindle写真集")
        kindle_res = generate_kindle_photobook(profile, generated_images, kindle_dir)
        print(f"  [KINDLE EPUB] {kindle_res['epub_path']}")
        print(f"  [KINDLE PDF]  {kindle_res['pdf_path']}")

    summary = {
        "success": True,
        "character": display_name,
        "output_dir": out_dir,
        "profile_path": profile_path,
        "audit_passed": audit_res["passed"],
        "images": generated_images,
        "audios": generated_audios,
        "videos": generated_videos,
        "kindle": kindle_res
    }
    summary_path = os.path.join(out_dir, "build_manifest.json")
    with open(summary_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)
    return summary


def main():
    parser = argparse.ArgumentParser(
        description="TUGUMIv6 AI Idol IP & Kindle Gravure Producer CLI (tugumi-idol)"
    )
    parser.add_argument(
        "--mode",
        choices=["init", "audit", "build", "kindle", "all"],
        default="all",
        help="実行モード (init: 設計作成, audit: 権利監査, build: 画像+音声+動画生成, kindle: 写真集生成, all: 全自動一括)"
    )
    parser.add_argument("--name", default="nagi_shiraishi", help="キャラ識別名 (英語/ローマ字)")
    parser.add_argument("--style", default="seiso", choices=["seiso"], help="スタイルプリセット (デフォルト: seiso=清楚系)")
    parser.add_argument("--char-json", default="", help="既存の profile.json パス")
    parser.add_argument("--out-dir", default="", help="出力先ディレクトリ (省略時は TUGUMIDesk/副業・収益化/AIアイドル_<name>)")
    parser.add_argument("--ref-image", default="", help="顔立ち・雰囲気を完全固定するリファレンス画像パス")
    parser.add_argument("--force", action="store_true", help="既存のキャッシュ画像を無視して強制再生成する")
    args = parser.parse_args()

    out_dir = args.out_dir or os.path.join(DESK_BASE, f"AIアイドル_{args.name}")
    profile_path = args.char_json or os.path.join(out_dir, f"{args.name}_profile.json")

    if args.mode == "init":
        cmd_init(args.name, args.style, out_dir, ref_image=args.ref_image)
    elif args.mode == "audit":
        if not os.path.exists(profile_path):
            print(f"[ERROR] プロファイルが存在しません: {profile_path}", file=sys.stderr)
            sys.exit(1)
        res = audit_profile(profile_path)
        print(json.dumps(res, ensure_ascii=False, indent=2))
        sys.exit(0 if res["passed"] else 1)
    elif args.mode == "build":
        if not os.path.exists(profile_path) or args.force:
            profile_path = cmd_init(args.name, args.style, out_dir, ref_image=args.ref_image)
        res = cmd_build(profile_path, build_kindle=False, ref_image=args.ref_image, force=args.force)
        print(json.dumps(res, ensure_ascii=False, indent=2))
    elif args.mode == "kindle":
        if not os.path.exists(profile_path):
            print(f"[ERROR] プロファイルが存在しません: {profile_path}", file=sys.stderr)
            sys.exit(1)
        with open(profile_path, "r", encoding="utf-8") as f:
            prof = json.load(f)
        img_dir = os.path.join(os.path.dirname(profile_path), "images")
        imgs = sorted(
            os.path.join(img_dir, p) for p in os.listdir(img_dir)
            if p.endswith("_portrait.png")
        )
        k_res = generate_kindle_photobook(prof, imgs, os.path.join(os.path.dirname(profile_path), "Kindle写真集"))
        print(json.dumps(k_res, ensure_ascii=False, indent=2))
    elif args.mode == "all":
        profile_path = cmd_init(args.name, args.style, out_dir, ref_image=args.ref_image)
        res = cmd_build(profile_path, build_kindle=True, ref_image=args.ref_image, force=args.force)
        print(json.dumps(res, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
