"""
TUGUMIv6 GitHealer & clone CLI Automated Test Suite
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tools.git_healer import GitHealer


def test_normalize_repo_url_standard():
    healer = GitHealer(verbose=False)

    # 1. Standard HTTPS
    url, owner, repo = healer.normalize_repo_url("https://github.com/psf/requests")
    assert url == "https://github.com/psf/requests.git"
    assert owner == "psf"
    assert repo == "requests"

    # 2. Standard HTTPS with .git
    url, owner, repo = healer.normalize_repo_url("https://github.com/psf/requests.git")
    assert url == "https://github.com/psf/requests.git"
    assert owner == "psf"
    assert repo == "requests"

    # 3. Short format (owner/repo)
    url, owner, repo = healer.normalize_repo_url("pallets/flask")
    assert url == "https://github.com/pallets/flask.git"
    assert owner == "pallets"
    assert repo == "flask"

    # 4. Without protocol (github.com/owner/repo)
    url, owner, repo = healer.normalize_repo_url("github.com/psf/black")
    assert url == "https://github.com/psf/black.git"
    assert owner == "psf"
    assert repo == "black"

    # 5. SSH Format
    url, owner, repo = healer.normalize_repo_url("git@github.com:torvalds/linux.git")
    assert url == "https://github.com/torvalds/linux.git"
    assert owner == "torvalds"
    assert repo == "linux"


def test_normalize_repo_url_browser_subpaths():
    healer = GitHealer(verbose=False)

    # 1. Browser URL with /tree/branch
    url, owner, repo = healer.normalize_repo_url("https://github.com/tiangolo/fastapi/tree/master/docs")
    assert url == "https://github.com/tiangolo/fastapi.git"
    assert owner == "tiangolo"
    assert repo == "fastapi"

    # 2. Browser URL with /blob/branch/file
    url, owner, repo = healer.normalize_repo_url("https://github.com/tiangolo/fastapi/blob/master/README.md")
    assert url == "https://github.com/tiangolo/fastapi.git"
    assert owner == "tiangolo"
    assert repo == "fastapi"

    # 3. Browser URL with trailing slash and query params
    url, owner, repo = healer.normalize_repo_url("https://github.com/pallets/click/?tab=readme-ov-file#installation")
    assert url == "https://github.com/pallets/click.git"
    assert owner == "pallets"
    assert repo == "click"

    # 4. Surrounded by quotes and whitespace
    url, owner, repo = healer.normalize_repo_url('  "https://github.com/python/cpython"  \n')
    assert url == "https://github.com/python/cpython.git"
    assert owner == "python"
    assert repo == "cpython"
