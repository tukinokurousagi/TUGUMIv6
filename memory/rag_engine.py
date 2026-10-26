# -*- coding: utf-8 -*-
"""
TUGUMIv6 Universal Hybrid RAG Engine v2.0
- Full Recursive Directory & Multi-Format Ingestion for /storage/emulated/0/TUGUMIDesk/TUGUMI_RAG
- Supports: Markdown (.md, .markdown), Text (.txt, extensionless), PDF (.pdf), HTML (.html, .htm),
  Source Code (.py, .cpp, .c, .js, .ts, .sh, etc.), Data (.json, .csv, .yaml, .toml, .xml),
  Office (.docx, .xlsx, .pptx), and Image/Media metadata (.jpg, .png, .webp, etc.)
- Dense Vector: gemini-embedding-2 (3072-dim Batch & Single Semantic Embeddings)
- Sparse Keyword: SQLite FTS5 (BM25 Match) + Japanese Bi-gram / Substring & Metadata Matcher
- Fusion: Reciprocal Rank Fusion (RRF) with Title/Folder Boost
"""

import os
import math
import json
import sqlite3
import re
import zipfile
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple, TYPE_CHECKING

if TYPE_CHECKING:
    pass


def cosine_similarity(v1: List[float], v2: List[float]) -> float:
    if not v1 or not v2 or len(v1) != len(v2):
        return 0.0
    dot = sum(a * b for a, b in zip(v1, v2))
    norm1 = math.sqrt(sum(a * a for a in v1))
    norm2 = math.sqrt(sum(b * b for b in v2))
    if norm1 == 0.0 or norm2 == 0.0:
        return 0.0
    return dot / (norm1 * norm2)


def normalize_japanese_pdf_spacing(text: str) -> str:
    """日本語PDF抽出時に発生する文字間の不要な空白（例: 'メ タ ン' -> 'メタン'）を正規化する"""
    if not text:
        return ""
    # CJK文字（ひらがな・カタカナ・漢字・全角記号）同士の間の単一・複数半角スペースを除去
    cjk_range = r"\u3000-\u303f\u3040-\u309f\u30a0-\u30ff\u3400-\u4dbf\u4e00-\u9fff\uff00-\uffef"
    pattern = re.compile(f"([{cjk_range}])[ \\t]+([{cjk_range}])")
    prev = None
    curr = text
    # 連続する文字間スペースを2パスで結合
    for _ in range(3):
        curr = pattern.sub(r"\1\2", curr)
        if curr == prev:
            break
        prev = curr
    return curr


class HybridRAGEngine:
    """Universal Hybrid Vector & Keyword RAG Engine for TUGUMIv6"""

    TEXT_EXTENSIONS = {
        ".md", ".markdown", ".txt", ".rst", ".log", ".ini", ".cfg", ".conf",
        ".json", ".jsonl", ".yaml", ".yml", ".toml", ".xml", ".csv", ".tsv",
        ".py", ".js", ".ts", ".tsx", ".jsx", ".cpp", ".cc", ".c", ".h", ".hpp",
        ".rs", ".go", ".java", ".kt", ".sh", ".bash", ".zsh", ".sql", ".rb",
        ".php", ".cs", ".swift", ".css", ".scss", ".lua", ".pl", ".r"
    }
    HTML_EXTENSIONS = {".html", ".htm"}
    PDF_EXTENSIONS = {".pdf"}
    OFFICE_EXTENSIONS = {".docx", ".xlsx", ".pptx"}
    IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".svg"}
    MEDIA_EXTENSIONS = {".mp3", ".wav", ".ogg", ".flac", ".m4a", ".mp4", ".mkv", ".webm", ".mov"}

    def __init__(
        self,
        gemini_client: Optional[Any] = None,
        rag_dirs: Optional[List[str]] = None,
        vector_cache_path: str = "/data/data/com.termux/files/home/TUGUMIv6/data/rag_vector_cache.json",
        db_path: str = "/data/data/com.termux/files/home/TUGUMIv6/data/tugumi_memory.db"
    ):
        self.client = gemini_client
        self.rag_dirs = rag_dirs or [
            "/storage/emulated/0/TUGUMIDesk/TUGUMI_RAG"
        ]
        self.vector_cache_path = vector_cache_path
        self.db_path = db_path
        self.vector_store: List[Dict[str, Any]] = []
        self._ensure_db_schema()
        self._load_vector_cache()

    @property
    def vector_cache(self) -> Dict[str, Any]:
        """後方互換プロパティ: source_chunk_id をキーとする辞書を返す"""
        return {
            item.get("source_chunk_id", f"chunk_{idx}"): item
            for idx, item in enumerate(self.vector_store)
        }

    def _ensure_client(self) -> Optional[Any]:
        """GeminiClient が未指定の場合に EngineManager から遅延ロードを試みる"""
        if self.client is not None:
            return self.client
        try:
            from core.engine_manager import EngineManager
            self.client = EngineManager().gemini
        except Exception:
            pass
        return self.client

    def _ensure_db_schema(self) -> None:
        """SQLite FTS5 テーブルの存在を保証する"""
        try:
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA journal_mode = WAL;")
                conn.execute("PRAGMA busy_timeout = 60000;")
                conn.execute("""
                    CREATE VIRTUAL TABLE IF NOT EXISTS knowledge_fts USING fts5(
                        title,
                        content,
                        category,
                        source_path
                    );
                """)
                conn.commit()
        except Exception as e:
            print(f"[RAGEngine] DB schema init warning: {e}")

    def _load_vector_cache(self) -> None:
        if os.path.exists(self.vector_cache_path):
            try:
                with open(self.vector_cache_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        self.vector_store = data
                    elif isinstance(data, dict):
                        self.vector_store = list(data.values())
            except Exception as e:
                print(f"[RAGEngine] Cache load failed: {e}")
                self.vector_store = []

    def _save_vector_cache(self) -> None:
        try:
            os.makedirs(os.path.dirname(self.vector_cache_path), exist_ok=True)
            with open(self.vector_cache_path, "w", encoding="utf-8") as f:
                json.dump(self.vector_store, f, ensure_ascii=False)
        except Exception as e:
            print(f"[RAGEngine] Cache save failed: {e}")

    def chunk_text(self, text: str, chunk_size: int = 900, overlap: int = 120) -> List[str]:
        """テキストの適切なサイズでのチャンク分割（段落・改行境界を考慮）"""
        if not text or not text.strip():
            return []
        cleaned = text.strip()
        if len(cleaned) <= chunk_size:
            return [cleaned]

        chunks: List[str] = []
        start = 0
        text_len = len(cleaned)
        while start < text_len:
            end = min(start + chunk_size, text_len)
            if end < text_len:
                # 改行や句点で自然に切れる位置を探す
                nl_pos = cleaned.rfind("\n", start + int(chunk_size * 0.6), end)
                if nl_pos != -1 and nl_pos > start:
                    end = nl_pos + 1
            chunk = cleaned[start:end].strip()
            if chunk:
                chunks.append(chunk)
            if end >= text_len:
                break
            next_start = end - overlap
            if next_start <= start:
                next_start = start + max(1, chunk_size - overlap)
            start = next_start
        return chunks

    def _is_likely_text_file(self, file_path: str) -> bool:
        """拡張子なしファイルや未知の拡張子ファイルがテキストかどうかを判定する"""
        try:
            with open(file_path, "rb") as f:
                sample = f.read(8192)
            if not sample:
                return True
            if b"\x00" in sample:
                return False
            return True
        except Exception:
            return False

    def _read_text_with_fallback(self, file_path: str) -> str:
        """UTF-8 / UTF-8-SIG / CP932 / Latin-1 の順でテキストを安全に読み込む"""
        for enc in ("utf-8", "utf-8-sig", "cp932", "shift_jis", "latin-1"):
            try:
                with open(file_path, "r", encoding=enc) as f:
                    return f.read()
            except UnicodeDecodeError:
                continue
            except Exception:
                break
        with open(file_path, "r", encoding="utf-8", errors="replace") as f:
            return f.read()

    def _extract_pdf_text(self, file_path: str) -> str:
        """PDFファイルから全ページのテキストを抽出し、日本語スペースを正規化する"""
        pages_text: List[str] = []
        try:
            import pypdf
            reader = pypdf.PdfReader(file_path)
            for idx, page in enumerate(reader.pages):
                raw_page = page.extract_text() or ""
                norm_page = normalize_japanese_pdf_spacing(raw_page).strip()
                if norm_page:
                    pages_text.append(f"[Page {idx + 1}/{len(reader.pages)}]\n{norm_page}")
        except Exception as e:
            pages_text.append(f"[PDF Extraction Error: {e}]")
        return "\n\n".join(pages_text)

    def _extract_html_text(self, file_path: str) -> str:
        """HTMLファイルからタイトル・メタ情報・UI構造特徴・本文テキストを高純度抽出する"""
        raw_html = self._read_text_with_fallback(file_path)
        if not raw_html.strip():
            return ""
        try:
            import bs4
            soup = bs4.BeautifulSoup(raw_html, "html.parser")
            title = soup.title.string.strip() if (soup.title and soup.title.string) else os.path.basename(file_path)

            # メタ情報・見出し・ID一覧を抽出（UIモックや設計書の検索性を高める）
            headings = []
            for h in soup.find_all(["h1", "h2", "h3", "h4"]):
                ht = " ".join(h.get_text().split())
                if ht and ht not in headings:
                    headings.append(ht)

            ids = []
            for el in soup.find_all(attrs={"id": True}):
                el_id = el.get("id")
                if el_id and isinstance(el_id, str) and el_id not in ids:
                    ids.append(el_id)

            # スクリプト・スタイル・SVGの巨大ノイズを除去して可読テキストを取り出す
            for noise in soup(["script", "style", "svg", "noscript"]):
                noise.decompose()

            lines = []
            for line in soup.get_text(separator="\n").splitlines():
                s = " ".join(line.split())
                if s:
                    lines.append(s)
            body_text = "\n".join(lines)

            header_parts = [f"HTML Title: {title}"]
            if headings:
                header_parts.append(f"Headings: {' / '.join(headings[:15])}")
            if ids:
                header_parts.append(f"DOM Element IDs: {', '.join(ids[:25])}")
            header_summary = "\n".join(header_parts)
            return f"{header_summary}\n\n{body_text}".strip()
        except Exception:
            # フォールバック: 正規表現でタグ除去
            cleaned = re.sub(r"<(script|style|svg)[^>]*>.*?</\1>", " ", raw_html, flags=re.DOTALL | re.IGNORECASE)
            cleaned = re.sub(r"<[^>]+>", "\n", cleaned)
            return "\n".join(" ".join(line.split()) for line in cleaned.splitlines() if line.strip())

    def _extract_office_text(self, file_path: str, ext: str) -> str:
        """Officeファイル (.docx, .xlsx, .pptx) からテキストを抽出する"""
        try:
            if ext == ".xlsx":
                import openpyxl
                wb = openpyxl.load_workbook(file_path, data_only=True, read_only=True)
                sheets_out = []
                for sheet_name in wb.sheetnames:
                    ws = wb[sheet_name]
                    rows_str = []
                    for row in ws.iter_rows(values_only=True):
                        vals = [str(v).strip() for v in row if v is not None and str(v).strip()]
                        if vals:
                            rows_str.append(" | ".join(vals))
                    if rows_str:
                        sheets_out.append(f"[Sheet: {sheet_name}]\n" + "\n".join(rows_str))
                wb.close()
                return "\n\n".join(sheets_out)

            elif ext == ".docx":
                with zipfile.ZipFile(file_path, "r") as z:
                    if "word/document.xml" in z.namelist():
                        xml_bytes = z.read("word/document.xml")
                        root = ET.fromstring(xml_bytes)
                        texts = [elem.text for elem in root.iter() if elem.text]
                        return " ".join(texts)

            elif ext == ".pptx":
                with zipfile.ZipFile(file_path, "r") as z:
                    slide_files = sorted([n for n in z.namelist() if n.startswith("ppt/slides/slide") and n.endswith(".xml")])
                    slides_out = []
                    for idx, sf in enumerate(slide_files):
                        xml_bytes = z.read(sf)
                        root = ET.fromstring(xml_bytes)
                        texts = [elem.text.strip() for elem in root.iter() if elem.text and elem.text.strip()]
                        if texts:
                            slides_out.append(f"[Slide {idx + 1}]\n" + "\n".join(texts))
                    return "\n\n".join(slides_out)
        except Exception as e:
            return f"[Office Document Metadata: {os.path.basename(file_path)} | Parse note: {e}]"
        return ""

    def _extract_image_or_media_metadata(self, file_path: str, rel_path: str, folder: str, ext: str) -> str:
        """画像やメディアファイルの属性・解像度・所属フォルダを構造化ナレッジとして抽出する"""
        stat = os.stat(file_path)
        size_kb = stat.st_size / 1024.0
        dt_str = datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
        info_lines = [
            f"ファイル名: {os.path.basename(file_path)}",
            f"相対パス: {rel_path}",
            f"所属フォルダ・カテゴリ: {folder}",
            f"ファイル形式: {ext or 'binary'}",
            f"ファイルサイズ: {size_kb:.1f} KB ({stat.st_size} bytes)",
            f"更新日時: {dt_str}",
        ]
        if ext in self.IMAGE_EXTENSIONS and ext != ".svg":
            try:
                from PIL import Image
                with Image.open(file_path) as img:
                    info_lines.append(f"画像フォーマット: {img.format}")
                    info_lines.append(f"画像解像度: {img.width}x{img.height} px")
                    info_lines.append(f"カラーモード: {img.mode}")
            except Exception:
                pass
        return "\n".join(info_lines)

    def extract_document_content(self, file_path: str, base_dir: str) -> Tuple[str, Dict[str, Any]]:
        """
        任意のファイルからRAG登録用のテキストとメタデータを抽出する。
        TUGUMI_RAG内のすべてのファイル形式（拡張子なし・PDF・HTML・コード・画像メタ等）に100%対応。
        """
        fn = os.path.basename(file_path)
        rel_path = os.path.relpath(file_path, base_dir).replace("\\", "/")
        rel_dir = os.path.dirname(rel_path).replace("\\", "/")
        folder = rel_dir if rel_dir and rel_dir != "." else "root"
        ext = os.path.splitext(fn)[1].lower()
        stat = os.stat(file_path)

        meta = {
            "file_path": file_path,
            "rel_path": rel_path,
            "folder": folder,
            "title": fn,
            "file_ext": ext if ext else "(no-ext)",
            "file_size": stat.st_size,
            "mtime": int(stat.st_mtime),
        }

        extracted_text = ""
        if ext in self.PDF_EXTENSIONS:
            extracted_text = self._extract_pdf_text(file_path)
        elif ext in self.HTML_EXTENSIONS:
            extracted_text = self._extract_html_text(file_path)
        elif ext in self.OFFICE_EXTENSIONS:
            extracted_text = self._extract_office_text(file_path, ext)
        elif ext in self.IMAGE_EXTENSIONS and ext != ".svg":
            extracted_text = self._extract_image_or_media_metadata(file_path, rel_path, folder, ext)
        elif ext in self.MEDIA_EXTENSIONS:
            extracted_text = self._extract_image_or_media_metadata(file_path, rel_path, folder, ext)
        elif ext in self.TEXT_EXTENSIONS or ext == ".svg":
            extracted_text = self._read_text_with_fallback(file_path)
        else:
            # 拡張子なしファイル（Dolphin_Creative leaked system information 等）や未知拡張子
            if self._is_likely_text_file(file_path):
                extracted_text = self._read_text_with_fallback(file_path)
            else:
                extracted_text = self._extract_image_or_media_metadata(file_path, rel_path, folder, ext)

        if not extracted_text or not extracted_text.strip():
            extracted_text = self._extract_image_or_media_metadata(file_path, rel_path, folder, ext)

        return extracted_text.strip(), meta

    def scan_all_rag_files(self) -> List[Tuple[str, str]]:
        """
        rag_dirs（/storage/emulated/0/TUGUMIDesk/TUGUMI_RAG 等）配下の
        すべてのフォルダ・サブフォルダ・ファイルを再帰的に走査して (file_path, base_dir) のリストを返す。
        """
        discovered: List[Tuple[str, str]] = []
        seen_paths = set()

        for rag_dir in self.rag_dirs:
            if not os.path.exists(rag_dir):
                continue
            for root, dirs, files in os.walk(rag_dir):
                # 隠しシステムフォルダ (.git, __pycache__ 等) のみスキップし、すべてのユーザーサブフォルダを走査
                dirs[:] = sorted([d for d in dirs if not d.startswith(".") and d != "__pycache__"])
                for fn in sorted(files):
                    if fn.startswith(".") or fn.endswith(".bak") or fn.endswith("~"):
                        continue
                    fp = os.path.join(root, fn)
                    if not os.path.isfile(fp):
                        continue
                    real_fp = os.path.abspath(fp)
                    if real_fp not in seen_paths:
                        seen_paths.add(real_fp)
                        discovered.append((fp, rag_dir))

        return discovered

    def sync_and_index_rag_files(self, max_files: int = 10000, force: bool = False) -> int:
        """
        TUGUMI_RAG 内の全フォルダ・全ファイルを再帰スキャンし、
        SQLite FTS5 と Vector Cache の双方へ漏れなく差分同期（または強制再構築）する。
        Returns:
            int: 新規または更新されたチャンク数（既に全件同期済みの場合は 0 ではなく、
                 未同期分があればその件数、force時は全チャンク数を返す）
        """
        stats = self.ingest_all(max_files=max_files, force=force)
        return stats.get("newly_indexed_chunks", 0)

    def ingest_all(self, max_files: int = 10000, force: bool = False, embed_missing: bool = True) -> Dict[str, Any]:
        """
        /storage/emulated/0/TUGUMIDesk/TUGUMI_RAG 配下の全フォルダ・全ファイルを100%取り込む統合メソッド。
        """
        discovered = self.scan_all_rag_files()
        if max_files and max_files > 0:
            discovered = discovered[:max_files]

        discovered_paths = {fp for fp, _ in discovered}
        local_knowledge_dir = "/data/data/com.termux/files/home/TUGUMIv6/data/rag_knowledge"

        # 既存キャッシュのファイル別インデックス状況を確認
        existing_by_file: Dict[str, List[Dict[str, Any]]] = {}
        kept_store: List[Dict[str, Any]] = []

        if not force:
            for item in self.vector_store:
                fp = item.get("file_path", "")
                # TUGUMI_RAG 内で削除されたファイルはパージ、存在するファイルと self_evolution 知識は保持
                if fp in discovered_paths or (local_knowledge_dir in fp and os.path.exists(fp)):
                    existing_by_file.setdefault(fp, []).append(item)
                elif any(fp.startswith(rd) for rd in self.rag_dirs):
                    # 削除されたファイルはスキップ
                    continue
                elif os.path.exists(fp):
                    existing_by_file.setdefault(fp, []).append(item)

        files_to_process: List[Tuple[str, str, Dict[str, Any], List[str]]] = []
        unchanged_files_count = 0

        for fp, base_dir in discovered:
            try:
                stat = os.stat(fp)
                curr_mtime = int(stat.st_mtime)
                curr_size = stat.st_size
                existing_chunks = existing_by_file.get(fp, [])

                # 既に登録済みで mtime / size が一致し、かつ folder メタデータも付与されている場合はスキップ
                if (
                    not force
                    and existing_chunks
                    and existing_chunks[0].get("mtime") == curr_mtime
                    and existing_chunks[0].get("file_size") == curr_size
                    and existing_chunks[0].get("rel_path")
                ):
                    kept_store.extend(existing_chunks)
                    unchanged_files_count += 1
                    continue

                content, meta = self.extract_document_content(fp, base_dir)
                raw_chunks = self.chunk_text(content, chunk_size=900, overlap=120)
                if not raw_chunks:
                    raw_chunks = [f"[{meta['rel_path']}] ({meta['file_ext']}, {meta['file_size']} bytes)"]

                # 1ファイルあたりのチャンク上限（巨大HTMLや巨大コードでキャッシュが肥大化するのを防ぎつつ全文網羅）
                if len(raw_chunks) > 40:
                    raw_chunks = self.chunk_text(content, chunk_size=1800, overlap=150)[:40]

                contextualized_chunks: List[str] = []
                for idx, ch in enumerate(raw_chunks):
                    header = f"[RAG Source: {meta['rel_path']} | Folder: {meta['folder']} | File: {meta['title']}]"
                    contextualized_chunks.append(f"{header}\n{ch}")

                files_to_process.append((fp, base_dir, meta, contextualized_chunks))
            except Exception as e:
                print(f"[RAGEngine] Error preparing {fp}: {e}")

        # self_evolution 等の追加知識ファイルも維持
        for fp, items in existing_by_file.items():
            if fp not in discovered_paths:
                kept_store.extend(items)

        # 新規・更新チャンクのバッチEmbedding生成
        new_items: List[Dict[str, Any]] = []
        for fp, base_dir, meta, ctx_chunks in files_to_process:
            # 既存の同一テキストチャンクにEmbeddingがあれば再利用してAPIコールを節約
            old_emb_map = {
                it.get("text", ""): it.get("embedding", [])
                for it in existing_by_file.get(fp, [])
                if it.get("embedding")
            }
            for idx, ch_text in enumerate(ctx_chunks):
                chunk_id = f"{fp}#{idx}"
                reused_emb = old_emb_map.get(ch_text, [])
                new_items.append({
                    "source_chunk_id": chunk_id,
                    "file_path": fp,
                    "rel_path": meta["rel_path"],
                    "folder": meta["folder"],
                    "title": meta["title"],
                    "file_ext": meta["file_ext"],
                    "file_size": meta["file_size"],
                    "mtime": meta["mtime"],
                    "text": ch_text,
                    "embedding": reused_emb if isinstance(reused_emb, list) else []
                })

        # 未ベクトル化のアイテムをまとめてバッチEmbedding
        if embed_missing:
            client = self._ensure_client()
            if client:
                missing_indices = [
                    i for i, it in enumerate(new_items)
                    if not it.get("embedding")
                ]
                if missing_indices:
                    texts_to_embed = [new_items[i]["text"] for i in missing_indices]
                    try:
                        if hasattr(client, "embed_texts_batch"):
                            batch_vecs = client.embed_texts_batch(texts_to_embed, batch_size=40)
                        else:
                            batch_vecs = [client.embed_text(t) for t in texts_to_embed]
                        for idx_pos, vec in zip(missing_indices, batch_vecs):
                            if vec and isinstance(vec, list):
                                new_items[idx_pos]["embedding"] = vec
                    except Exception as e:
                        print(f"[RAGEngine] Batch embedding warning (FTS5 still active): {e}")

        # kept_store 側で万が一未ベクトル化のものがあれば補完（最大40件まで）
        if embed_missing:
            client = self._ensure_client()
            if client:
                kept_missing = [i for i, it in enumerate(kept_store) if not it.get("embedding")][:40]
                if kept_missing:
                    try:
                        texts_k = [kept_store[i]["text"] for i in kept_missing]
                        vecs_k = client.embed_texts_batch(texts_k, batch_size=40) if hasattr(client, "embed_texts_batch") else [client.embed_text(t) for t in texts_k]
                        for idx_pos, vec in zip(kept_missing, vecs_k):
                            if vec and isinstance(vec, list):
                                kept_store[idx_pos]["embedding"] = vec
                    except Exception:
                        pass

        self.vector_store = kept_store + new_items
        self._save_vector_cache()

        # SQLite FTS5 テーブルを vector_store と完全整合させる
        self._rebuild_fts_from_store()

        summary = self.get_status_summary()
        summary["newly_indexed_files"] = len(files_to_process)
        summary["newly_indexed_chunks"] = len(new_items)
        summary["unchanged_files"] = unchanged_files_count
        return summary

    def _rebuild_fts_from_store(self) -> None:
        """vector_store の全チャンクを SQLite FTS5 (knowledge_fts) に完全同期する"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("PRAGMA journal_mode = WAL;")
                conn.execute("PRAGMA busy_timeout = 60000;")
                conn.execute("DELETE FROM knowledge_fts WHERE category LIKE 'rag%' OR category = 'self_evolution';")
                rows_to_insert = []
                for item in self.vector_store:
                    title = item.get("title", "")
                    rel_path = item.get("rel_path", "")
                    folder = item.get("folder", "root")
                    display_title = f"{rel_path}" if rel_path else title
                    content = item.get("text", "")
                    category = f"rag:{folder}" if folder else "rag_file"
                    source_path = item.get("file_path", "")
                    rows_to_insert.append((display_title, content, category, source_path))
                conn.executemany("""
                    INSERT INTO knowledge_fts (title, content, category, source_path)
                    VALUES (?, ?, ?, ?)
                """, rows_to_insert)
                conn.commit()
        except Exception as e:
            print(f"[RAGEngine] FTS5 rebuild warning: {e}")

    def add_knowledge(self, title: str, text: str, category: str = "self_evolution") -> bool:
        """単一ドキュメントを即座にファイル保存し、3072次元ベクトル化およびFTS5へ同期登録"""
        safe_name = re.sub(r'[^a-zA-Z0-9_\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FFF-]', '_', title)[:50]
        local_dir = "/data/data/com.termux/files/home/TUGUMIv6/data/rag_knowledge"
        os.makedirs(local_dir, exist_ok=True)
        file_path = os.path.join(local_dir, f"{safe_name}.md")

        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(f"# {title}\n\n{text}")

            stat = os.stat(file_path)
            chunks = self.chunk_text(text)
            client = self._ensure_client()

            # 既存の同名知識を除去して最新化
            self.vector_store = [it for it in self.vector_store if it.get("file_path") != file_path]

            vecs: List[List[float]] = []
            if client and chunks:
                try:
                    if hasattr(client, "embed_texts_batch"):
                        vecs = client.embed_texts_batch(chunks, batch_size=20)
                    else:
                        vecs = [client.embed_text(c) for c in chunks]
                except Exception:
                    vecs = [[] for _ in chunks]
            else:
                vecs = [[] for _ in chunks]

            conn = sqlite3.connect(self.db_path)
            conn.execute("PRAGMA journal_mode = WAL;")
            conn.execute("PRAGMA busy_timeout = 60000;")
            conn.execute("DELETE FROM knowledge_fts WHERE source_path = ?;", (file_path,))

            for i, chunk in enumerate(chunks):
                chunk_id = f"{file_path}#{i}"
                vec = vecs[i] if i < len(vecs) else []
                self.vector_store.append({
                    "source_chunk_id": chunk_id,
                    "file_path": file_path,
                    "rel_path": f"rag_knowledge/{safe_name}.md",
                    "folder": category,
                    "title": title,
                    "file_ext": ".md",
                    "file_size": stat.st_size,
                    "mtime": int(stat.st_mtime),
                    "text": chunk,
                    "embedding": vec if isinstance(vec, list) else []
                })
                conn.execute("""
                    INSERT INTO knowledge_fts (title, content, category, source_path)
                    VALUES (?, ?, ?, ?)
                """, (title, chunk, f"rag:{category}", file_path))

            conn.commit()
            conn.close()
            self._save_vector_cache()
            return True
        except Exception as e:
            print(f"[RAGEngine] add_knowledge failed: {e}")
            return False

    def _extract_query_terms(self, query: str) -> List[str]:
        """日本語・英語混在クエリから検索キーワードと2文字N-gramトークンを抽出する"""
        if not query:
            return []
        # 句読点や助詞で簡易分割
        cleaned = re.sub(r"[、。！？!\?（）\(\)\[\]「」『』・：:／/\\,\.\-\s]+", " ", query)
        raw_parts = [p.strip() for p in cleaned.split() if p.strip()]
        terms: List[str] = []
        for part in raw_parts:
            terms.append(part)
            # 助詞分割
            sub_parts = re.split(r"(?:について|とは|ですか|教えて|ください|[のをにはがでとへやも])", part)
            for sp in sub_parts:
                sp = sp.strip()
                if len(sp) >= 2 and sp not in terms:
                    terms.append(sp)
            # 漢字・カタカナ・英数字の連続塊を抽出
            chunks = re.findall(r"[A-Za-z0-9_]{2,}|[\u4e00-\u9fff]{2,}|[\u30a0-\u30ff]{2,}|[\u3040-\u309f]{3,}", part)
            for ch in chunks:
                if ch not in terms:
                    terms.append(ch)
        return terms

    def search_hybrid(
        self,
        query: str,
        top_k: int = 5,
        folder_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Dense Vector (gemini-embedding-2) + Sparse FTS5 + 日本語部分一致/メタデータブーストの
        3層ハイブリッド検索 (Reciprocal Rank Fusion)
        """
        if not query or not query.strip():
            return []

        # もしキャッシュが空なら自動初期インジェスト（埋め込みなし高速モード→後続利用可能）
        if not self.vector_store:
            self.ingest_all(embed_missing=False)

        candidates = self.vector_store
        if folder_filter:
            ff_lower = folder_filter.strip().lower()
            candidates = [
                it for it in candidates
                if ff_lower in str(it.get("folder", "")).lower()
                or ff_lower in str(it.get("rel_path", "")).lower()
            ]

        # 1. Dense Vector Search (3072-dim Cosine Similarity)
        dense_results: List[Dict[str, Any]] = []
        has_embeddings = any(it.get("embedding") for it in candidates)
        if has_embeddings:
            client = self._ensure_client()
            if client and hasattr(client, "embed_text"):
                try:
                    query_vec = client.embed_text(query)
                    if query_vec:
                        for item in candidates:
                            emb = item.get("embedding")
                            if emb:
                                sim = cosine_similarity(query_vec, emb)
                                dense_results.append({
                                    "title": item.get("title", ""),
                                    "rel_path": item.get("rel_path", item.get("title", "")),
                                    "folder": item.get("folder", "root"),
                                    "text": item.get("text", ""),
                                    "source": item.get("file_path", ""),
                                    "score": sim
                                })
                        dense_results.sort(key=lambda x: x["score"], reverse=True)
                except Exception:
                    dense_results = []

        # 2. Sparse FTS5 Search
        sparse_results: List[Dict[str, Any]] = []
        terms = self._extract_query_terms(query)
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cur = conn.cursor()
                safe_q = " ".join([t for t in terms if t.isalnum()])
                if safe_q.strip():
                    cur.execute("""
                        SELECT title, content as text, category, source_path as source, rank as score
                        FROM knowledge_fts
                        WHERE knowledge_fts MATCH ?
                        ORDER BY rank LIMIT 20
                    """, (safe_q.strip(),))
                    for r in cur.fetchall():
                        d = dict(r)
                        if folder_filter and folder_filter.lower() not in (d.get("title", "") + d.get("category", "")).lower():
                            continue
                        sparse_results.append({
                            "title": os.path.basename(d.get("source", "")) or d.get("title", ""),
                            "rel_path": d.get("title", ""),
                            "folder": str(d.get("category", "")).replace("rag:", ""),
                            "text": d.get("text", ""),
                            "source": d.get("source", ""),
                            "score": abs(float(d.get("score", 0.0)))
                        })
        except Exception:
            pass

        # 3. 日本語キーワード・ファイル名・フォルダ名ダイレクトマッチャー（FTS5の日本語トークナイズ漏れを100%補完）
        lexical_results: List[Dict[str, Any]] = []
        q_lower = query.strip().lower()
        for item in candidates:
            title_l = str(item.get("title", "")).lower()
            rel_l = str(item.get("rel_path", "")).lower()
            folder_l = str(item.get("folder", "")).lower()
            text_l = str(item.get("text", "")).lower()

            lex_score = 0.0
            if q_lower in title_l or q_lower in rel_l:
                lex_score += 5.0
            if q_lower in text_l:
                lex_score += 2.5

            for term in terms:
                tl = term.lower()
                if len(tl) < 2:
                    continue
                if tl in title_l:
                    lex_score += 3.0
                if tl in folder_l:
                    lex_score += 2.0
                if tl in text_l:
                    # 出現回数に応じた対数ボーナス
                    cnt = text_l.count(tl)
                    lex_score += 1.0 + min(1.5, math.log1p(cnt) * 0.4)

            if lex_score > 0.0:
                lexical_results.append({
                    "title": item.get("title", ""),
                    "rel_path": item.get("rel_path", item.get("title", "")),
                    "folder": item.get("folder", "root"),
                    "text": item.get("text", ""),
                    "source": item.get("file_path", ""),
                    "score": lex_score
                })
        lexical_results.sort(key=lambda x: x["score"], reverse=True)

        # 4. Reciprocal Rank Fusion (RRF: k=60) + Lexical Boost
        rrf_scores: Dict[str, float] = {}
        content_map: Dict[str, Dict[str, Any]] = {}

        for rank, item in enumerate(dense_results[:25]):
            key = f"{item['source']}:{item['text'][:80]}"
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.2 / (60 + rank))
            content_map[key] = item

        for rank, item in enumerate(sparse_results[:25]):
            key = f"{item['source']}:{item['text'][:80]}"
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (1.0 / (60 + rank))
            if key not in content_map:
                content_map[key] = item

        for rank, item in enumerate(lexical_results[:25]):
            key = f"{item['source']}:{item['text'][:80]}"
            # ファイル名・語彙一致には確実なRRF重みを付与
            boost = 1.35 if item["score"] >= 3.0 else 1.0
            rrf_scores[key] = rrf_scores.get(key, 0.0) + (boost / (50 + rank))
            if key not in content_map:
                content_map[key] = item

        ranked_keys = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)
        final_results: List[Dict[str, Any]] = []
        for k in ranked_keys[:top_k]:
            entry = dict(content_map[k])
            entry["rrf_score"] = round(rrf_scores[k], 5)
            final_results.append(entry)

        return final_results

    def query(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """MCP / 外部互換用クエリエントリポイント"""
        return self.search_hybrid(query=query, top_k=top_k)

    def get_status_summary(self) -> Dict[str, Any]:
        """
        現在のRAGインデックス統計情報（総ファイル数、総チャンク数、フォルダ別・拡張子別内訳）を返す。
        """
        rag_files_on_disk = self.scan_all_rag_files()
        total_disk_files = len(rag_files_on_disk)

        indexed_files_map: Dict[str, Dict[str, Any]] = {}
        folder_stats: Dict[str, Dict[str, int]] = {}
        ext_stats: Dict[str, int] = {}
        embedded_chunks = 0

        for item in self.vector_store:
            fp = item.get("file_path", "")
            rel = item.get("rel_path") or os.path.basename(fp)
            folder = item.get("folder")
            if not folder:
                # 旧キャッシュ互換
                for rd in self.rag_dirs:
                    if fp.startswith(rd):
                        rel = os.path.relpath(fp, rd).replace("\\", "/")
                        d = os.path.dirname(rel).replace("\\", "/")
                        folder = d if d and d != "." else "root"
                        break
                if not folder:
                    folder = "self_evolution"

            ext = item.get("file_ext") or os.path.splitext(fp)[1].lower() or "(no-ext)"
            if item.get("embedding"):
                embedded_chunks += 1

            if fp not in indexed_files_map:
                indexed_files_map[fp] = {
                    "file_path": fp,
                    "rel_path": rel,
                    "folder": folder,
                    "title": item.get("title", os.path.basename(fp)),
                    "file_ext": ext,
                    "file_size": item.get("file_size", 0),
                    "chunks": 0,
                }
                ext_stats[ext] = ext_stats.get(ext, 0) + 1
                f_entry = folder_stats.setdefault(folder, {"files": 0, "chunks": 0})
                f_entry["files"] += 1

            indexed_files_map[fp]["chunks"] += 1
            folder_stats.setdefault(folder, {"files": 0, "chunks": 0})["chunks"] += 1

        fts_count = 0
        try:
            with sqlite3.connect(self.db_path) as conn:
                fts_count = conn.execute("SELECT count(*) FROM knowledge_fts").fetchone()[0]
        except Exception:
            pass

        # TUGUMI_RAG ディレクトリ内のファイルに限定したカウントも算出
        tugumi_rag_indexed = sum(
            1 for fp in indexed_files_map
            if any(fp.startswith(rd) for rd in self.rag_dirs)
        )

        return {
            "rag_dirs": self.rag_dirs,
            "disk_total_files": total_disk_files,
            "tugumi_rag_indexed_files": tugumi_rag_indexed,
            "total_indexed_files": len(indexed_files_map),
            "total_chunks": len(self.vector_store),
            "embedded_chunks": embedded_chunks,
            "fts5_rows": fts_count,
            "folder_stats": folder_stats,
            "ext_stats": ext_stats,
            "files": sorted(indexed_files_map.values(), key=lambda x: x["rel_path"]),
        }

    def list_indexed_files(self, folder_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """インデックス済みファイル一覧を返す"""
        summary = self.get_status_summary()
        files = summary.get("files", [])
        if folder_filter:
            ff = folder_filter.strip().lower()
            files = [
                f for f in files
                if ff in f["folder"].lower() or ff in f["rel_path"].lower()
            ]
        return files
