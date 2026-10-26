# -*- coding: utf-8 -*-
"""
TUGUMIv6 Autonomous Media & Content Monetization Engine
- Discovers high-traffic tech topics (arXiv, GitHub Trending, AI News)
- Generates high-quality Japanese Markdown articles with SEO optimization
- Deploys automatically to GitHub Pages / Cloudflare Pages via Git
- Injects affiliate and ad placeholders safely
"""

import os
import time
import subprocess
from typing import Dict, Any
from core.gemini_client import GeminiClient

class AutoMediaEngine:
    """Autonomous Tech Media Generator & Publisher"""
    def __init__(
        self,
        gemini_client: GeminiClient,
        output_dir: str = "/data/data/com.termux/files/home/TUGUMIv6/data/media_articles"
    ):
        self.client = gemini_client
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_article(self, topic: str, affiliate_tag: str = "tugumi-affiliate-22") -> Dict[str, Any]:
        """Gemini 3.8 Flash を駆使してSEOに強い高付加価値記事を自動生成"""
        prompt = f"""
あなたは最高峰のテックジャーナリストです。
以下のテーマについて、プロフェッショナルかつ読者が引き込まれる日本語の解説記事（Markdown形式）を作成してください。

テーマ: {topic}
構成要件:
1. 読者の課題を突く魅力的なタイトル (H1)
2. リード文（結論と読者が得られるメリット）
3. 背景と最新トレンドの解説 (H2)
4. 実証コード例またはステップバイステップの具体的手順 (H2)
5. おすすめツールや関連書籍の紹介セクション (アフィリエイト枠: [関連推奨ツール・書籍はこちら](https://example.com/item?tag={affiliate_tag}))
6. まとめと今後の展望 (H2)

モックコードや手抜きは禁止し、実用的なコード例を含めてください。
"""
        article_text = self.client.generate_content(prompt=prompt)
        timestamp = int(time.time())
        filename = f"article_{timestamp}.md"
        filepath = os.path.join(self.output_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(article_text)

        return {
            "status": "success",
            "file": filepath,
            "topic": topic,
            "length": len(article_text),
            "timestamp": timestamp
        }

    def deploy_to_git(self, repo_dir: str, commit_message: str = "Auto-update tech article") -> Dict[str, Any]:
        """GitHub Pages / Cloudflare Pages へGitコミット＆プッシュ"""
        if not os.path.exists(os.path.join(repo_dir, ".git")):
            return {"status": "skipped", "message": f"{repo_dir} is not a git repository"}

        cmds = [
            f"cd {repo_dir} && git add .",
            f"cd {repo_dir} && git commit -m '{commit_message}' || true",
            f"cd {repo_dir} && git push origin main || true"
        ]
        results = []
        for cmd in cmds:
            res = subprocess.run(cmd, shell=True, capture_output=True, text=True)
            results.append(res.stdout.strip() or res.stderr.strip())

        return {"status": "completed", "logs": results}
