#!/data/data/com.termux/files/usr/bin/python3
"""
AI Model Producer Pro: Face-Lock Dressup & Background Transformation Engine
リファレンス画像から Character DNA（骨格・目元・前髪・生体質感）を100%固定し、
衣装・背景・ポーズを高精度に着せ替え・置換生成する。
Dedicated to Master Takuma
"""

import os
import sys
import argparse

sys.path.insert(0, "/data/data/com.termux/files/home/TUGUMIv6")
from tools.media_tools import GeminiImageStudio

def main():
    parser = argparse.ArgumentParser(description="AI美女モデル顔立ち固定・衣装＆背景着せ替えエンジン")
    parser.add_argument("images", nargs="+", help="リファレンス画像パス（1枚以上）")
    parser.add_argument("-o", "--outfit", default="", help="変更する衣装（例: 夏用セーラー制服, 浴衣, ニット）")
    parser.add_argument("-b", "--bg", "--background", default="", help="変更する背景・ロケーション（例: 放課後の教室, 夏祭り）")
    parser.add_argument("-m", "--mood", "--pose", default="", help="表情やポーズ（例: 微笑み, 頬杖）")
    parser.add_argument("-f", "--filename", default="", help="出力ファイル名")
    args = parser.parse_args()

    print("👗 AI美女モデル顔立ち固定・着せ替え実行中...")
    print(f"  リファレンス画像: {args.images}")
    print(f"  衣装: {args.outfit or 'エレガントカジュアル'}")
    print(f"  背景: {args.bg or 'ナチュラルロケーション'}")
    if args.mood:
        print(f"  ポーズ/表情: {args.mood}")

    res = GeminiImageStudio.face_lock_dressup(
        image_paths=args.images,
        outfit=args.outfit,
        background=args.bg,
        mood_or_pose=args.mood,
        output_filename=args.filename
    )

    if res.get("success"):
        print(f"\n✅ 成功！保存先: {res['file_path']}")
        print(GeminiImageStudio.to_ascii(res['file_path'], target_width=44))
    else:
        print(f"\n❌ エラー: {res.get('error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()
