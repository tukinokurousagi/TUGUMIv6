"""TUGUMIv6 Dual Interface Package"""

def run_cli(*args, **kwargs):
    from .cli.main import run_cli as _run_cli
    return _run_cli(*args, **kwargs)

def run_web_server(*args, **kwargs):
    from .web.web_server import run_web_server as _run_web_server
    return _run_web_server(*args, **kwargs)

__all__ = ["run_cli", "run_web_server"]
