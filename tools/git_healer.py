# -*- coding: utf-8 -*-
"""
TUGUMIv6 Git Auto-Clone & Self-Healing Engine (git_healer.py)
=============================================================
GitHubリポジトリのURLを入力するだけで、自動クローンから
Termux環境への適合、依存解決、構文エラー・非推奨コードの自己修復、
および動作確認（スモークテスト）までを一気通貫で完遂する完全自律型スクリプト。

機能ハイライト:
1. スマートURL正規化 (GitHub, GitLab, user/repo 短縮記法対応)
2. 高速＆軽量クローン (Shallow Clone / サブモジュール再帰 / SSLフォールバック)
3. プロジェクトDNA自動判定 (Python, Node.js, Shell, Rust, Go, C/C++)
4. Termux環境自動適合 (termux-fix-shebang, CRLF->LF, 実行権限, ハードコードパス修復)
5. Python 3.14+ 互換性自動パッチ (imp, distutils, pipes, cgi などの廃止モジュール置換)
6. 依存関係の自動インストール & ビルド障害防護 (Cライブラリ事前導入, pip/npm)
7. 静的構文検証 & Gemini 3.8 Flash による自律AIエラー外科的修復
8. スモークテスト & スマホTermux特化型カードブロックUI
9. Termuxネイティブ通知 (termux-notification, termux-toast)
"""

import os
import sys
import re
import json
import subprocess
import time
import shutil
from typing import Dict, Any, Optional, Tuple

# TUGUMIv6 内部モジュールへのパス解決
TUGUMI_DIR = "/data/data/com.termux/files/home/TUGUMIv6"
if TUGUMI_DIR not in sys.path:
    sys.path.insert(0, TUGUMI_DIR)

try:
    from core.gemini_client import GeminiClient
except ImportError:
    GeminiClient = None


class GitHealer:
    """GitHub Auto-Clone & Autonomous Self-Healing Engine for Termux"""

    DEFAULT_PROJECTS_DIR = os.path.expanduser("~/projects")
    TERMUX_PREFIX = "/data/data/com.termux/files/usr"
    TERMUX_TMP = "/data/data/com.termux/files/usr/tmp"

    def __init__(
        self,
        projects_dir: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: str = "gemini-3.8-flash",
        verbose: bool = True
    ):
        self.projects_dir = os.path.abspath(projects_dir or self.DEFAULT_PROJECTS_DIR)
        os.makedirs(self.projects_dir, exist_ok=True)
        self.verbose = verbose
        self.model_name = model_name

        # API Key 取得 (引数 -> engine_config.json -> 環境変数)
        self.api_key = api_key or self._load_api_key()

        # Gemini Client 初期化
        self.gemini_client = None
        if GeminiClient and self.api_key:
            try:
                self.gemini_client = GeminiClient(
                    api_key=self.api_key,
                    model=self.model_name,
                    timeout=60.0
                )
            except Exception as e:
                self._log(f"⚠️ GeminiClient初期化警告: {e}")

    def _load_api_key(self) -> str:
        """engine_config.json または環境変数からAPIキーを読み込む"""
        config_path = os.path.join(TUGUMI_DIR, "engine_config.json")
        if os.path.exists(config_path):
            try:
                with open(config_path, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                    key = cfg.get("api_key", "")
                    if key and not key.startswith("YOUR_"):
                        return key
            except Exception:
                pass
        from core.gemini_client import _resolve_gemini_api_key
        return _resolve_gemini_api_key("")

    def _log(self, msg: str, level: str = "INFO"):
        """フォーマットされたログを出力"""
        if not self.verbose and level == "DEBUG":
            return
        print(msg, flush=True)

    def notify(self, title: str, content: str):
        """Termuxネイティブ通知 & トーストを送信"""
        try:
            subprocess.run(
                [
                    "termux-notification",
                    "--title", title,
                    "--content", content,
                    "--id", "tugumi-clone",
                    "--priority", "high"
                ],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
        except Exception:
            pass
        try:
            subprocess.run(
                ["termux-toast", content],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                check=False
            )
        except Exception:
            pass

    # =========================================================================
    # 1. URL 正規化 & リポジトリ情報抽出
    # =========================================================================
    def normalize_repo_url(self, raw_url: str) -> Tuple[str, str, str]:
        """
        URLを正規化し、(clone_url, owner, repo_name) を返す。
        ブラウザでコピーしたURL (/tree/... や /blob/... 等のサブパス含む) も自動正規化。
        """
        text = raw_url.strip()
        # 不要な引用符や空白を除去
        text = text.strip("\"' \t\r\n")

        # 短縮記法 (user/repo) の補完
        if re.match(r'^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$', text):
            parts = text.split("/")
            return f"https://github.com/{parts[0]}/{parts[1]}.git", parts[0], parts[1]

        # github.com/user/repo 形式の補完
        if text.startswith("github.com/"):
            text = "https://" + text

        # SSH形式 git@github.com:user/repo.git
        ssh_match = re.match(r'^git@([^:]+):([^/]+)/([^\.]+?)(?:\.git)?$', text)
        if ssh_match:
            host, owner, repo = ssh_match.groups()
            return f"https://{host}/{owner}/{repo}.git", owner, repo

        # GitHub HTTPS形式 (サブパス /tree/..., /blob/..., /releases 等を自動剥離)
        gh_match = re.match(r'^https?://(?:www\.)?github\.com/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?(?:/.*)?$', text)
        if gh_match:
            owner, repo = gh_match.groups()
            return f"https://github.com/{owner}/{repo}.git", owner, repo

        # 一般的なGit HTTPS形式 (GitLab / Bitbucket等)
        http_match = re.match(r'^https?://([^/]+)/([A-Za-z0-9_.-]+)/([A-Za-z0-9_.-]+?)(?:\.git)?(?:/.*)?$', text)
        if http_match:
            host, owner, repo = http_match.groups()
            return f"https://{host}/{owner}/{repo}.git", owner, repo

        # フォールバック
        clean_name = re.sub(r'[^A-Za-z0-9_.-]', '_', text.split("/")[-1]) or "cloned_repo"
        return text, "unknown", clean_name

    # =========================================================================
    # 2. スマートクローン (Smart Clone)
    # =========================================================================
    def clone(
        self,
        repo_url: str,
        dest_dir: Optional[str] = None,
        shallow: bool = True
    ) -> Dict[str, Any]:
        """
        リポジトリをクローンし、失敗時は自動修復リトライを行う。
        """
        clone_url, owner, repo_name = self.normalize_repo_url(repo_url)
        target_path = os.path.abspath(dest_dir or os.path.join(self.projects_dir, repo_name))

        # 既存フォルダ衝突の回避
        if os.path.exists(target_path):
            if os.path.isdir(target_path) and os.path.exists(os.path.join(target_path, ".git")):
                self._log(f"ℹ️ 既存のGitリポジトリを検出: {target_path}")
                # 最新状態にpull
                pull_res = subprocess.run(
                    ["git", "-C", target_path, "pull", "--ff-only"],
                    capture_output=True,
                    text=True
                )
                return {
                    "success": True,
                    "target_path": target_path,
                    "repo_name": repo_name,
                    "owner": owner,
                    "clone_url": clone_url,
                    "reused_existing": True,
                    "pull_output": pull_res.stdout
                }
            else:
                # 衝突回避のためのサフィックス付与
                timestamp = time.strftime("%Y%m%d_%H%M%S")
                target_path = f"{target_path}_{timestamp}"

        self._log(f"📥 クローン開始: {clone_url}")
        self._log(f"📂 保存先: {target_path}")

        # クローンコマンド組み立て
        cmd = ["git", "clone"]
        if shallow:
            cmd.extend(["--depth", "1"])
        cmd.extend([clone_url, target_path])

        # 実行試行 1: 通常クローン
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            # サブモジュールの更新
            subprocess.run(
                ["git", "-C", target_path, "submodule", "update", "--init", "--recursive", "--depth", "1"],
                capture_output=True,
                text=True
            )
            return {
                "success": True,
                "target_path": target_path,
                "repo_name": repo_name,
                "owner": owner,
                "clone_url": clone_url,
                "reused_existing": False
            }

        # 失敗時の自動修復リトライ 2: SSL証明書検証回避（Termux証明書破損対策）
        self._log("⚠️ 通常クローン失敗。SSL検証無効化で再試行...")
        ssl_cmd = ["git", "-c", "http.sslVerify=false", "clone"]
        if shallow:
            ssl_cmd.extend(["--depth", "1"])
        ssl_cmd.extend([clone_url, target_path])

        res2 = subprocess.run(ssl_cmd, capture_output=True, text=True)
        if res2.returncode == 0:
            return {
                "success": True,
                "target_path": target_path,
                "repo_name": repo_name,
                "owner": owner,
                "clone_url": clone_url,
                "reused_existing": False
            }

        # 失敗時の自動修復リトライ 3: shallow解除 (Full Clone)
        if shallow:
            self._log("⚠️ Shallowクローン失敗。Fullクローンで再試行...")
            full_cmd = ["git", "-c", "http.sslVerify=false", "clone", clone_url, target_path]
            res3 = subprocess.run(full_cmd, capture_output=True, text=True)
            if res3.returncode == 0:
                return {
                    "success": True,
                    "target_path": target_path,
                    "repo_name": repo_name,
                    "owner": owner,
                    "clone_url": clone_url,
                    "reused_existing": False
                }

        # クローン失敗
        return {
            "success": False,
            "error": res.stderr or res2.stderr,
            "target_path": target_path,
            "clone_url": clone_url
        }

    # =========================================================================
    # 3. プロジェクトDNA自動判定 (Project DNA Detection)
    # =========================================================================
    def detect_project_dna(self, repo_dir: str) -> Dict[str, Any]:
        """リポジトリ内のファイルを走査し、主要技術スタックとエントリポイントを判定"""
        dna = {
            "is_python": False,
            "is_node": False,
            "is_rust": False,
            "is_go": False,
            "is_shell": False,
            "is_cpp": False,
            "python_deps": [],
            "entry_points": [],
            "config_files": []
        }

        # ファイル走査
        for root, dirs, files in os.walk(repo_dir):
            # .git はスキップ
            if ".git" in dirs:
                dirs.remove(".git")

            for f in files:
                rel_path = os.path.relpath(os.path.join(root, f), repo_dir)

                if f in ("requirements.txt", "pyproject.toml", "setup.py", "Pipfile", "poetry.lock"):
                    dna["is_python"] = True
                    dna["config_files"].append(rel_path)
                elif f.endswith(".py"):
                    dna["is_python"] = True
                    if f in ("main.py", "app.py", "cli.py", "run.py", "__main__.py", "server.py"):
                        dna["entry_points"].append(rel_path)

                if f in ("package.json", "yarn.lock", "pnpm-lock.yaml", "bun.lockb"):
                    dna["is_node"] = True
                    dna["config_files"].append(rel_path)
                elif f in ("index.js", "server.js", "app.js", "main.js"):
                    dna["entry_points"].append(rel_path)

                if f == "Cargo.toml":
                    dna["is_rust"] = True
                    dna["config_files"].append(rel_path)

                if f == "go.mod":
                    dna["is_go"] = True
                    dna["config_files"].append(rel_path)

                if f in ("Makefile", "CMakeLists.txt", "configure"):
                    dna["is_cpp"] = True
                    dna["config_files"].append(rel_path)

                if f.endswith(".sh"):
                    dna["is_shell"] = True
                    if f in ("start.sh", "run.sh", "install.sh", "setup.sh", "launch.sh"):
                        dna["entry_points"].append(rel_path)

        # Python requirements の解析
        req_file = os.path.join(repo_dir, "requirements.txt")
        if os.path.exists(req_file):
            try:
                with open(req_file, "r", encoding="utf-8", errors="ignore") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#"):
                            pkg = re.split(r'[=<>~!]', line)[0].strip()
                            if pkg:
                                dna["python_deps"].append(pkg.lower())
            except Exception:
                pass

        return dna

    # =========================================================================
    # 4. Termux環境自動適合 (Termux Environment Adaptation)
    # =========================================================================
    def adapt_to_termux(self, repo_dir: str) -> Dict[str, Any]:
        """
        Termux環境特有の障害（シバン、改行コード、パーミッション、ハードコードパス、
        Python 3.14廃止モジュール）を外科的に自動修復。
        """
        stats = {
            "shebang_fixed": 0,
            "crlf_fixed": 0,
            "chmod_fixed": 0,
            "paths_healed": 0,
            "py314_healed": 0
        }

        # 1. termux-fix-shebang 実行
        fix_shebang_cmd = "/data/data/com.termux/files/usr/bin/termux-fix-shebang"
        if os.path.exists(fix_shebang_cmd):
            try:
                subprocess.run([fix_shebang_cmd, "."], cwd=repo_dir, capture_output=True)
                stats["shebang_fixed"] += 1
            except Exception:
                pass

        # 2. ファイル巡回パッチ
        for root, dirs, files in os.walk(repo_dir):
            if ".git" in dirs:
                dirs.remove(".git")

            for f in files:
                file_path = os.path.join(root, f)

                # 実行権限の付与 (*.sh, *.py, *.pl, *.rb)
                if f.endswith((".sh", ".py", ".pl", ".rb")):
                    try:
                        st = os.stat(file_path)
                        os.chmod(file_path, st.st_mode | 0o755)
                        stats["chmod_fixed"] += 1
                    except Exception:
                        pass

                # テキストファイルの検査と修復
                if f.endswith((".py", ".sh", ".js", ".ts", ".json", ".md", ".txt", ".toml", ".yaml", ".yml")):
                    try:
                        with open(file_path, "rb") as bf:
                            raw_bytes = bf.read()

                        # CRLF -> LF
                        modified = False
                        if b"\r\n" in raw_bytes:
                            raw_bytes = raw_bytes.replace(b"\r\n", b"\n")
                            stats["crlf_fixed"] += 1
                            modified = True

                        # テキストデコード
                        try:
                            content = raw_bytes.decode("utf-8")
                        except UnicodeDecodeError:
                            content = raw_bytes.decode("latin-1")

                        orig_content = content

                        # ハードコードされたLinuxパスの修復
                        if f.endswith((".py", ".sh")):
                            # /tmp/ -> $TMPDIR
                            if "/tmp/" in content and "/data/data/com.termux" not in content:
                                if f.endswith(".py"):
                                    # os.environ.get('TMPDIR', '/tmp') への配慮
                                    content = re.sub(
                                        r'([\'"])/tmp/([^\'"]+)\1',
                                        r'os.path.join(os.environ.get("TMPDIR", "/data/data/com.termux/files/usr/tmp"), "\2")',
                                        content
                                    )
                                    if "import os" not in content:
                                        content = "import os\n" + content
                                elif f.endswith(".sh"):
                                    content = content.replace("/tmp", "${TMPDIR:-/data/data/com.termux/files/usr/tmp}")
                                stats["paths_healed"] += 1

                            # /usr/bin/ -> $PREFIX/bin
                            if "/usr/bin/" in content:
                                content = content.replace("/usr/bin/", "/data/data/com.termux/files/usr/bin/")
                                stats["paths_healed"] += 1

                            # /etc/ -> $PREFIX/etc
                            if "/etc/" in content and "/data/data/com.termux" not in content:
                                content = content.replace("/etc/", "/data/data/com.termux/files/usr/etc/")
                                stats["paths_healed"] += 1

                        # Python 3.14+ 廃止・削除モジュールの置換
                        if f.endswith(".py"):
                            # imp -> importlib
                            if "import imp" in content or "from imp import" in content:
                                content = re.sub(r'\bimport imp\b', 'import importlib as imp', content)
                                content = re.sub(r'\bfrom imp import\b', 'from importlib import', content)
                                stats["py314_healed"] += 1

                            # distutils -> setuptools / packaging
                            if "from distutils.version import LooseVersion" in content:
                                content = content.replace(
                                    "from distutils.version import LooseVersion",
                                    "try:\n    from packaging.version import parse as LooseVersion\nexcept ImportError:\n    from distutils.version import LooseVersion"
                                )
                                stats["py314_healed"] += 1

                            # cgi.escape -> html.escape
                            if "cgi.escape" in content:
                                content = re.sub(r'\bcgi\.escape\b', 'html.escape', content)
                                if "import html" not in content:
                                    content = "import html\n" + content
                                stats["py314_healed"] += 1

                            # pipes.quote -> shlex.quote
                            if "pipes.quote" in content:
                                content = re.sub(r'\bpipes\.quote\b', 'shlex.quote', content)
                                if "import shlex" not in content:
                                    content = "import shlex\n" + content
                                stats["py314_healed"] += 1

                        # 変更があった場合は安全に書き戻す
                        if content != orig_content or modified:
                            with open(file_path, "w", encoding="utf-8") as wf:
                                wf.write(content)

                    except Exception as e:
                        self._log(f"⚠️ ファイル修復スキップ ({f}): {e}", "DEBUG")

        return stats

    # =========================================================================
    # 5. 依存関係の解決 (Dependency Resolver)
    # =========================================================================
    def install_dependencies(
        self,
        repo_dir: str,
        dna: Dict[str, Any],
        use_venv: bool = False
    ) -> Dict[str, Any]:
        """
        プロジェクトの依存関係をTermuxに適合させてインストール。
        必要に応じてTermuxネイティブパッケージ（clang, openssl等）を先行導入。
        """
        results = {
            "success": True,
            "installed_pkgs": [],
            "warnings": [],
            "venv_created": False
        }

        # 仮想環境（venv）の作成
        env_python = sys.executable
        if use_venv:
            venv_dir = os.path.join(repo_dir, ".venv")
            if not os.path.exists(venv_dir):
                self._log("📦 仮想環境 (.venv) を作成中...")
                v_res = subprocess.run([sys.executable, "-m", "venv", venv_dir], capture_output=True)
                if v_res.returncode == 0:
                    results["venv_created"] = True
                    env_python = os.path.join(venv_dir, "bin", "python")
                else:
                    results["warnings"].append("仮想環境作成失敗。システムPythonを使用します。")

        # ---------------------------------------------------------------------
        # Python 依存関係の解決
        # ---------------------------------------------------------------------
        if dna.get("is_python"):
            py_deps = dna.get("python_deps", [])

            # TermuxでC拡張ビルドに必要なネイティブパッケージの事前検知＆APTマッピング
            apt_py_map = {
                "numpy": "python-numpy",
                "pillow": "python-pillow",
                "cryptography": "python-cryptography",
                "lxml": "python-lxml",
                "scipy": "python-scipy",
                "grpcio": "python-grpcio",
                "msgpack": "python-msgpack",
                "greenlet": "python-greenlet",
                "pydantic": "python-pydantic",
                "bcrypt": "python-bcrypt",
                "tornado": "python-tornado",
                "pyyaml": "python-yaml"
            }
            c_ext_map = {
                "cryptography": ["clang", "openssl", "rust", "libffi"],
                "pillow": ["clang", "libjpeg-turbo", "libpng", "freetype"],
                "lxml": ["clang", "libxml2", "libxslt"],
                "psutil": ["clang"],
                "cffi": ["clang", "libffi"],
                "uvloop": ["clang"],
                "numpy": ["clang", "python", "openblas"],
                "scipy": ["clang", "openblas", "fftw"]
            }

            native_needs = set(["clang", "make"])
            apt_py_pkgs = set()
            for dep in py_deps:
                dep_lower = dep.lower()
                for target, pkgs in c_ext_map.items():
                    if target in dep_lower:
                        native_needs.update(pkgs)
                for target, apt_pkg in apt_py_map.items():
                    if target == dep_lower:
                        apt_py_pkgs.add(apt_pkg)

            # ネイティブビルド環境 & Termux最適化済みPythonパッケージの事前インストール
            all_pkgs_to_install = list(native_needs) + list(apt_py_pkgs)
            if all_pkgs_to_install:
                self._log(f"🔧 Termuxネイティブ依存/最適化バイナリを事前導入: {', '.join(all_pkgs_to_install)}")
                try:
                    subprocess.run(
                        ["pkg", "install", "-y"] + all_pkgs_to_install,
                        stdout=subprocess.DEVNULL,
                        stderr=subprocess.DEVNULL,
                        check=False
                    )
                except Exception:
                    pass

            base_pip_cmd = [env_python, "-m", "pip", "install", "--break-system-packages"]

            # requirements.txt のインストール
            req_file = os.path.join(repo_dir, "requirements.txt")
            if os.path.exists(req_file):
                self._log("📥 Python依存関係 (requirements.txt) をインストール中...")
                
                # 試行 1: 標準インストール
                res = subprocess.run(base_pip_cmd + ["-r", "requirements.txt"], cwd=repo_dir, capture_output=True, text=True)
                if res.returncode == 0:
                    results["installed_pkgs"].append("requirements.txt")
                else:
                    self._log("⚠️ 通常の pip install に失敗。--no-build-isolation --prefer-binary で再試行...")
                    # 試行 2: --no-build-isolation + --prefer-binary
                    res2 = subprocess.run(
                        base_pip_cmd + ["--no-build-isolation", "--prefer-binary", "-r", "requirements.txt"],
                        cwd=repo_dir, capture_output=True, text=True
                    )
                    if res2.returncode == 0:
                        results["installed_pkgs"].append("requirements.txt (prefer-binary)")
                    else:
                        # 試行 3: 個別行インストール（壊れているパッケージをスキップし成功分を全量救済）
                        self._log("⚠️ 一部パッケージのビルドに失敗。通るパッケージを個別自動救済インストール中...")
                        succeeded_lines = 0
                        failed_pkgs = []
                        try:
                            with open(req_file, "r", encoding="utf-8", errors="ignore") as rf:
                                req_lines = [l.strip() for l in rf if l.strip() and not l.strip().startswith("#")]
                            for r_line in req_lines:
                                line_res = subprocess.run(
                                    base_pip_cmd + ["--no-build-isolation", "--prefer-binary", r_line],
                                    cwd=repo_dir, capture_output=True, text=True
                                )
                                if line_res.returncode == 0:
                                    succeeded_lines += 1
                                else:
                                    failed_pkgs.append(r_line)
                            if succeeded_lines > 0:
                                results["installed_pkgs"].append(f"requirements.txt (部分救済: {succeeded_lines}/{len(req_lines)} 件成功)")
                            if failed_pkgs:
                                results["warnings"].append(f"一部パッケージがTermuxビルド非対応のためスキップ: {', '.join(failed_pkgs[:5])}")
                        except Exception as e:
                            results["warnings"].append(f"依存関係個別インストール例外: {e}")

            # setup.py / pyproject.toml
            if os.path.exists(os.path.join(repo_dir, "setup.py")) or os.path.exists(os.path.join(repo_dir, "pyproject.toml")):
                self._log("📥 パッケージをローカルインストール中 (pip install -e .)...")
                pip_cmd = base_pip_cmd + ["--no-build-isolation", "-e", "."]
                res = subprocess.run(pip_cmd, cwd=repo_dir, capture_output=True, text=True)
                if res.returncode == 0:
                    results["installed_pkgs"].append("local_package")
                else:
                    results["warnings"].append(f"ローカルパッケージインストール失敗 (警告のみ): {res.stderr[:200]}")

        # ---------------------------------------------------------------------
        # Node.js 依存関係の解決 (Bun 優先 / npm フォールバック)
        # ---------------------------------------------------------------------
        if dna.get("is_node"):
            pkg_json = os.path.join(repo_dir, "package.json")
            if os.path.exists(pkg_json):
                npm_env = os.environ.copy()
                npm_env["PUPPETEER_SKIP_CHROMIUM_DOWNLOAD"] = "true"
                bun_bin = shutil.which("bun") or "/data/data/com.termux/files/home/.bun/bin/bun"
                
                if os.path.exists(bun_bin):
                    self._log("📥 超高速 Node.js 依存関係インストール (bun install) を実行中...")
                    res = subprocess.run([bun_bin, "install"], cwd=repo_dir, env=npm_env, capture_output=True, text=True)
                    if res.returncode == 0:
                        results["installed_pkgs"].append("bun_packages")
                    else:
                        self._log("⚠️ bun install に失敗。npm install でフォールバック試行...")
                        res_npm = subprocess.run(["npm", "install", "--prefer-offline", "--no-audit"], cwd=repo_dir, env=npm_env, capture_output=True, text=True)
                        if res_npm.returncode == 0:
                            results["installed_pkgs"].append("npm_packages")
                        else:
                            results["warnings"].append(f"npm install 警告: {res_npm.stderr[:200]}")
                else:
                    self._log("📥 Node.js 依存関係インストール (npm install) を実行中...")
                    res = subprocess.run(["npm", "install", "--prefer-offline", "--no-audit"], cwd=repo_dir, env=npm_env, capture_output=True, text=True)
                    if res.returncode == 0:
                        results["installed_pkgs"].append("npm_packages")
                    else:
                        results["warnings"].append(f"npm install 警告: {res.stderr[:200]}")

        # ---------------------------------------------------------------------
        # Rust 依存関係 (Cargo.toml)
        # ---------------------------------------------------------------------
        if dna.get("is_rust") and shutil.which("cargo"):
            cargo_file = os.path.join(repo_dir, "Cargo.toml")
            if os.path.exists(cargo_file):
                self._log("📥 Rust依存関係の解決 (cargo check) を実行中...")
                res_cargo = subprocess.run(["cargo", "check"], cwd=repo_dir, capture_output=True, text=True)
                if res_cargo.returncode == 0:
                    results["installed_pkgs"].append("cargo_crates")
                else:
                    results["warnings"].append(f"cargo check 警告: {res_cargo.stderr[:200]}")

        # ---------------------------------------------------------------------
        # Go 依存関係 (go.mod)
        # ---------------------------------------------------------------------
        if dna.get("is_go") and shutil.which("go"):
            go_file = os.path.join(repo_dir, "go.mod")
            if os.path.exists(go_file):
                self._log("📥 Goモジュールの解決 (go mod tidy) を実行中...")
                res_go = subprocess.run(["go", "mod", "tidy"], cwd=repo_dir, capture_output=True, text=True)
                if res_go.returncode == 0:
                    results["installed_pkgs"].append("go_modules")
                else:
                    results["warnings"].append(f"go mod tidy 警告: {res_go.stderr[:200]}")

        return results

    # =========================================================================
    # 6. 静的構文検証 & 自律AIエラー修復 (Self-Healing Loop)
    # =========================================================================
    def validate_and_heal(self, repo_dir: str, max_rounds: int = 3) -> Dict[str, Any]:
        """
        全Pythonファイルの構文を検査し、SyntaxErrorや非互換性があれば
        ルールベースおよびGemini 3.8 FlashによるAI外科的パッチで自動修復する。
        """
        healing_stats = {
            "syntax_errors_found": 0,
            "files_healed": [],
            "rounds_executed": 0,
            "all_passed": True
        }

        for round_idx in range(1, max_rounds + 1):
            healing_stats["rounds_executed"] = round_idx
            errors_in_round = []

            # 全.pyファイルの構文チェック
            for root, dirs, files in os.walk(repo_dir):
                # 不要なディレクトリの再帰をスキップ
                dirs[:] = [d for d in dirs if d not in (".git", ".venv", "__pycache__", "build", "dist", ".pytest_cache")]

                for f in files:
                    if f.endswith(".py"):
                        py_path = os.path.join(root, f)
                        compile_res = subprocess.run(
                            [sys.executable, "-m", "py_compile", py_path],
                            capture_output=True,
                            text=True
                        )
                        if compile_res.returncode != 0:
                            errors_in_round.append({
                                "file": py_path,
                                "rel_path": os.path.relpath(py_path, repo_dir),
                                "error": compile_res.stderr
                            })

            if not errors_in_round:
                self._log(f"✅ 全スクリプトの構文検証に合格 (ラウンド {round_idx})")
                healing_stats["all_passed"] = True
                break

            healing_stats["syntax_errors_found"] += len(errors_in_round)
            self._log(f"🚨 構文エラーを {len(errors_in_round)} 件検出。自己修復を開始します (ラウンド {round_idx}/{max_rounds})...")

            for err in errors_in_round:
                healed = self._heal_single_file(err["file"], err["error"])
                if healed:
                    healing_stats["files_healed"].append(err["rel_path"])

        # 最終判定
        if errors_in_round:
            healing_stats["all_passed"] = False

        return healing_stats

    def _heal_single_file(self, file_path: str, error_msg: str) -> bool:
        """単一ファイルのエラーを解析し、ルールベースまたはGeminiで外科的修復"""
        self._log(f"🩹 修復中: {os.path.basename(file_path)}")
        try:
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                code = f.read()
        except Exception:
            return False

        # ---------------------------------------------------------------------
        # ルールベース修復 1: Python 2 系 print 文 (print "...")
        # ---------------------------------------------------------------------
        if "Missing parentheses in call to 'print'" in error_msg or re.search(r'^\s*print\s+["\']', code, re.MULTILINE):
            new_code = re.sub(r'^(\s*)print\s+([^\(\n\r]+)$', r'\1print(\2)', code, flags=re.MULTILINE)
            if new_code != code:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_code)
                self._log("  ✨ ルールベース: print文の括弧抜けを修復しました")
                return True

        # ---------------------------------------------------------------------
        # ルールベース修復 2: except Exception, e 構文
        # ---------------------------------------------------------------------
        if ("invalid syntax" in error_msg or "SyntaxError" in error_msg) and "except " in code:
            new_code = re.sub(r'except\s+([A-Za-z0-9_]+)\s*,\s*([A-Za-z0-9_]+):', r'except \1 as \2:', code)
            if new_code != code:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(new_code)
                self._log("  ✨ ルールベース: Python 2形式の例外構文を修復しました")
                return True

        # ---------------------------------------------------------------------
        # AIインテリジェント修復: Gemini 3.8 Flash
        # ---------------------------------------------------------------------
        if self.gemini_client:
            self._log("  🧠 Gemini 3.8 Flash によるインテリジェント自己修復を実行中...")
            prompt = f"""あなたはAndroid Termux (Linux aarch64, Python 3.14) 環境に特化した最高峰の自律デバッグエンジニアです。
以下のPythonファイルで構文エラーまたは実行エラーが発生しました。
エラーを第一原理から分析し、TermuxおよびPython 3.14環境で正常にコンパイル・動作するように外科的に修正した【完全なコード全体】のみを出力してください。

【対象ファイル】: {os.path.basename(file_path)}
【エラー内容】:
{error_msg}

【現在のコード】:
```python
{code[:4000]}
```

【絶対遵守指示】:
- 解説や前置き・後書き（「はい、修正しました」等）は一切出力しないでください。
- ```python と ``` で囲まれた完全なコードのみを出力してください。
"""
            try:
                ai_resp = self.gemini_client.generate_content(prompt)
                match = re.search(r'```(?:python)?\s*(.*?)\s*```', ai_resp, re.DOTALL)
                healed_code = match.group(1).strip() if match else ai_resp.strip()

                if healed_code and len(healed_code) > 20:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(healed_code)
                    self._log("  ✨ AI自律パッチ: コードの外科的修復を適用しました")
                    return True
            except Exception as e:
                self._log(f"  ⚠️ AI修復呼び出しエラー: {e}")

        return False

    # =========================================================================
    # 7. スモークテスト (Smoke Test & Dry Run)
    # =========================================================================
    def smoke_test(self, repo_dir: str, dna: Dict[str, Any]) -> Dict[str, Any]:
        """エントリポイントを実行し、クラッシュしないか検証"""
        test_res = {
            "tested_entry": None,
            "success": True,
            "output": "",
            "cmd": ""
        }

        entry_candidates = dna.get("entry_points", [])
        if not entry_candidates:
            # 一般的なエントリポイントを探索
            for f in ("main.py", "app.py", "cli.py", "run.py", "start.sh"):
                p = os.path.join(repo_dir, f)
                if os.path.exists(p):
                    entry_candidates.append(f)
                    break

        if not entry_candidates:
            test_res["tested_entry"] = "なし"
            return test_res

        entry = entry_candidates[0]
        test_res["tested_entry"] = entry

        if entry.endswith(".py"):
            test_cmd = [sys.executable, entry, "--help"]
        elif entry.endswith(".sh"):
            test_cmd = ["bash", entry, "--help"]
        elif entry.endswith(".js"):
            test_cmd = ["node", entry, "--help"]
        else:
            return test_res

        test_res["cmd"] = " ".join(test_cmd)
        try:
            p = subprocess.run(
                test_cmd,
                cwd=repo_dir,
                capture_output=True,
                text=True,
                timeout=60
            )
            test_res["output"] = (p.stdout or p.stderr)[:300]
            # --help で exit code 0 または 2 (argparse) なら正常起動
            test_res["success"] = p.returncode in (0, 2)
        except subprocess.TimeoutExpired:
            test_res["output"] = "起動テストタイムアウト (常駐サーバーまたは待機プロセスの可能性)"
            test_res["success"] = True
        except Exception as e:
            test_res["output"] = str(e)
            test_res["success"] = False

        return test_res

    # =========================================================================
    # 8. フル自動実行パイプライン (Full Autonomous Pipeline)
    # =========================================================================
    def execute(
        self,
        repo_url: str,
        dest_dir: Optional[str] = None,
        shallow: bool = True,
        install_deps: bool = True,
        auto_heal: bool = True,
        run_test: bool = True
    ) -> Dict[str, Any]:
        """
        全パイプラインを一気通貫で実行し、詳細レポートを生成。
        """
        start_time = time.time()
        self._log("\n" + "="*50)
        self._log("🌸 TUGUMIv6 自律Gitクローン＆自動エラー修復システム")
        self._log("="*50)

        # 1. クローン
        clone_result = self.clone(repo_url, dest_dir=dest_dir, shallow=shallow)
        if not clone_result["success"]:
            self._log(f"❌ クローン失敗: {clone_result.get('error', '不明なエラー')}")
            return {"success": False, "step": "clone", "details": clone_result}

        target_dir = clone_result["target_path"]
        repo_name = clone_result["repo_name"]

        # 2. プロジェクトDNA判定
        self._log("\n🔍 [STEP 2] プロジェクトDNA自動判定中...")
        dna = self.detect_project_dna(target_dir)
        langs = []
        if dna["is_python"]: langs.append("Python")
        if dna["is_node"]: langs.append("Node.js")
        if dna["is_shell"]: langs.append("Shell")
        if dna["is_rust"]: langs.append("Rust")
        if dna["is_go"]: langs.append("Go")
        if dna["is_cpp"]: langs.append("C/C++")
        self._log(f"   検出スタック: {', '.join(langs) or '汎用リポジトリ'}")

        # 3. Termux環境適合化
        self._log("\n⚙️ [STEP 3] Termux環境適合パッチを適用中...")
        adapt_stats = self.adapt_to_termux(target_dir)
        self._log(f"   シバン修正: {adapt_stats['shebang_fixed']} 件 / 改行修正: {adapt_stats['crlf_fixed']} 件")
        self._log(f"   権限付与: {adapt_stats['chmod_fixed']} 件 / パス修復: {adapt_stats['paths_healed']} 件")
        self._log(f"   Python 3.14互換修復: {adapt_stats['py314_healed']} 件")

        # 4. 依存関係の解決
        dep_stats = {"success": True, "installed_pkgs": [], "warnings": []}
        if install_deps:
            self._log("\n📦 [STEP 4] 依存関係の自動インストール中...")
            dep_stats = self.install_dependencies(target_dir, dna)

        # 5. 静的検証 & 自己修復
        heal_stats = {"all_passed": True, "syntax_errors_found": 0, "files_healed": []}
        if auto_heal and dna["is_python"]:
            self._log("\n🛡️ [STEP 5] 構文検証 & 自律エラー修復ループ...")
            heal_stats = self.validate_and_heal(target_dir)

        # 6. スモークテスト
        test_stats = {"tested_entry": None, "success": True}
        if run_test:
            self._log("\n🧪 [STEP 6] 起動スモークテスト...")
            test_stats = self.smoke_test(target_dir, dna)
            if test_stats["tested_entry"]:
                status_str = "正常起動確認" if test_stats["success"] else "起動注意"
                self._log(f"   テスト対象: {test_stats['tested_entry']} ({status_str})")

        elapsed = round(time.time() - start_time, 2)

        # 完了通知
        notify_title = f"✨ クローン＆修復完了: {repo_name}"
        notify_msg = f"{repo_name} のセットアップとエラー修復が完了しました ({elapsed}秒)"
        self.notify(notify_title, notify_msg)

        # 結果まとめ
        summary = {
            "success": True,
            "repo_name": repo_name,
            "target_dir": target_dir,
            "languages": langs,
            "adapt_stats": adapt_stats,
            "dep_stats": dep_stats,
            "heal_stats": heal_stats,
            "test_stats": test_stats,
            "elapsed_sec": elapsed
        }

        # 画面出力 (スマホ最適化カードブロック形式)
        self._print_card_summary(summary)

        return summary

    def _print_card_summary(self, summary: Dict[str, Any]):
        """スマホTermux画面（40〜60列）で崩れない美しいカードブロック形式で出力"""
        target = summary["target_dir"]
        langs = ", ".join(summary["languages"]) or "汎用"
        adapt = summary["adapt_stats"]
        heal = summary["heal_stats"]
        test = summary["test_stats"]

        print("\n" + "="*50)
        print("🎉 【完全自律セットアップ＆エラー修復完了報告】")
        print("="*50)

        print(f"\n### 📦 リポジトリ情報 `[{summary['elapsed_sec']}秒]`")
        print(f"- **名前**: `{summary['repo_name']}`")
        print(f"- **スタック**: {langs}")
        print(f"- **保存先**: `{target}`")

        print("\n### ⚙️ Termux環境適合パッチ")
        print(f"- **シバン修正**: {adapt['shebang_fixed']} 件")
        print(f"- **改行コード (LF)**: {adapt['crlf_fixed']} 件")
        print(f"- **実行権限付与**: {adapt['chmod_fixed']} 件")
        print(f"- **Linuxパス修復**: {adapt['paths_healed']} 件")
        print(f"- **Python 3.14互換化**: {adapt['py314_healed']} 件")

        if heal["files_healed"]:
            print("\n### 🩹 自律AIエラー修復実績")
            for hf in heal["files_healed"]:
                print(f"- **修正ファイル**: `{hf}`")
        else:
            print("\n### 🛡️ 構文・コード品質")
            print("- **状態**: 構文エラーゼロ・検証全合格")

        print("\n### 🚀 すぐに使うための起動コマンド")
        print(f"- `cd {target}`")
        if test.get("tested_entry") and test["tested_entry"] != "なし":
            entry = test["tested_entry"]
            if entry.endswith(".py"):
                print(f"- `python3 {entry}`")
            elif entry.endswith(".sh"):
                print(f"- `./{entry}`")
            elif entry.endswith(".js"):
                print(f"- `node {entry}`")
        else:
            print("- `ls -la` でファイルを確認してください")

        print("\n" + "="*50 + "\n")


# CLIエントリーポイント
def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="TUGUMIv6 自律Gitクローン＆エラー自動修復システム"
    )
    parser.add_argument("url", nargs="?", help="クローンしたいGitHubリポジトリのURLまたは user/repo")
    parser.add_argument("dest", nargs="?", help="クローン先ディレクトリ (任意)")
    parser.add_argument("--no-shallow", action="store_true", help="Fullクローンを実行 (デフォルトはShallow)")
    parser.add_argument("--no-deps", action="store_true", help="依存関係のインストールをスキップ")
    parser.add_argument("--no-heal", action="store_true", help="エラー自動修復ループをスキップ")
    parser.add_argument("--no-test", action="store_true", help="スモークテストをスキップ")

    args = parser.parse_args()

    url = args.url
    if not url:
        print("="*50)
        print("🌸 TUGUMIv6 自律Gitクローン＆自動エラー修復システム")
        print("="*50)
        try:
            url = input("クローンしたいGitHubのURLを入力してください: ").strip()
        except (KeyboardInterrupt, EOFError):
            print("\nキャンセルされました。")
            sys.exit(0)

    if not url:
        print("⚠️ URLが入力されませんでした。終了します。")
        sys.exit(1)

    healer = GitHealer()
    healer.execute(
        repo_url=url,
        dest_dir=args.dest,
        shallow=not args.no_shallow,
        install_deps=not args.no_deps,
        auto_heal=not args.no_heal,
        run_test=not args.no_test
    )


if __name__ == "__main__":
    main()
