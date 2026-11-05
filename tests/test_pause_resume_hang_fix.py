# -*- coding: utf-8 -*-
"""
TUGUMIv6 「タスク実行中 → 一時中断 → 追加プロンプト投入 → 再開」ハングアップ根絶回帰テスト

外部API通信は一切行わない（フェイク Agent / 一時 SQLite / 一時ファイルのみ使用）。
  1. AntigravitySession: 旧ターンの conversation.cancel() が永久ブロックしても再開ターンが完走する
  2. 旧ストリームの close() が再開後の新ターンを巻き込まない（所有者ガード）
  3. TaskStateMachine / StreamContext / guarded_call
  4. LoopGuard: 可変要素の正規化・類似度・周期検知・再開時リセット
  5. SQLiteMemory / RAGEngine: 並行書込・中断時ロック残留なし・Outbox整合
  6. SystemVerifier Fail-Closed
  7. ContextCompressor Pinned Context
"""
import asyncio
import json
import os
import sqlite3
import sys
import threading
import time

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import core.antigravity_sdk as sdk_mod  # noqa: E402
from core.loop_guard import LoopGuard, normalize_args_repr  # noqa: E402
from core.supervisor import TaskState, TaskStateMachine, guarded_call  # noqa: E402
from core.verifier import SecurityVerificationFailure, SystemVerifier  # noqa: E402
from memory.rag_engine import HybridRAGEngine as RAGEngine  # noqa: E402
from memory.sqlite_memory import SQLiteMemory  # noqa: E402
from persona.context_compressor import ContextCompressor  # noqa: E402

agy_types = sdk_mod.agy_types


# ───────────────────────── 1/2. AntigravitySession ─────────────────────────
class _FakeResp:
    def __init__(self, chunks):
        self.chunks = chunks


class _FakeConversation:
    """cancel() が永久にブロックする（= 再開時ハングの根本原因を再現）会話"""

    def __init__(self, hang_cancel: bool):
        self.hang_cancel = hang_cancel
        self.cancel_calls = 0

    async def cancel(self):
        self.cancel_calls += 1
        if self.hang_cancel:
            await asyncio.sleep(3600)


class _FakeAgent:
    hang_cancel = True

    def __init__(self, config):
        self.conversation = _FakeConversation(type(self).hang_cancel)

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def chat(self, prompt):
        async def _gen():
            if "steer" in prompt:
                yield agy_types.Text(step_index=0, text="steer-ok")
                return
            yield agy_types.Text(step_index=0, text="first-chunk")
            await asyncio.sleep(3600)  # 長時間ツール/推論の途中で中断される旧ターン

        return _FakeResp(_gen())


class _FakeEngine:
    def build_config(self, **kwargs):
        return object()


@pytest.fixture
def fake_session(monkeypatch):
    monkeypatch.setattr(sdk_mod, "Agent", _FakeAgent)
    sess = sdk_mod.AntigravitySession(engine=_FakeEngine(), system_instruction="x", mode="light")
    yield sess
    sess.close()


def _collect(stream, timeout):
    out, deadline = [], time.time() + timeout
    for ctype, cdata in stream:
        out.append((ctype, cdata))
        if time.time() > deadline:
            break
    return out


def test_resume_after_esc_does_not_hang_even_if_conversation_cancel_blocks(fake_session):
    s1 = fake_session.chat_stream("long task")
    first = None
    for ctype, cdata in s1:
        if ctype == "text":
            first = cdata
            break
    assert first == "first-chunk"

    # CLI main.py と同一の再開手順: cancel_active_task → stream.close → 追加プロンプトで新ターン
    fake_session.cancel()
    s1.close()

    t0 = time.time()
    chunks = _collect(fake_session.chat_stream("steer: 短く挨拶"), timeout=20)
    elapsed = time.time() - t0
    texts = [d for t, d in chunks if t == "text"]
    assert "steer-ok" in texts, f"再開ターンが完走しなかった: {chunks}"
    assert elapsed < 15, f"再開が遅すぎる(ハング疑い): {elapsed:.1f}s"


def test_old_stream_close_does_not_cancel_new_turn(fake_session):
    s1 = fake_session.chat_stream("long task")
    for ctype, _ in s1:
        if ctype == "text":
            break
    fake_session.cancel()  # ESC
    # 旧ストリームを close せず放置したまま新ターンへ（Web: 旧SSEの切断が遅れて届くケース）
    s2 = fake_session.chat_stream("steer: hi")
    got = []
    for ctype, cdata in s2:
        got.append((ctype, cdata))
        if ctype == "text":
            break
    # ここで遅れて旧ストリームが close されても、新ターンの所有権(current_out_q)を奪ってはならない
    owner_before = fake_session.current_out_q
    s1.close()
    assert fake_session.current_out_q is owner_before
    assert ("text", "steer-ok") in got
    for _ in s2:
        pass


# ───────────────────────── 3. TaskStateMachine ─────────────────────────
def test_state_machine_pause_resume_cancel_and_stream_rebind():
    from core.loop_guard import default_loop_guard

    tsm = TaskStateMachine()
    flushed = []
    tsm.register_flush_hook(lambda: flushed.append(1))

    ctx1 = tsm.begin_turn()
    assert tsm.state == TaskState.RUNNING and ctx1.is_current()
    tsm.pause()
    assert tsm.state == TaskState.PAUSED

    default_loop_guard.record_call("t", "same-arg")
    tsm.cancel("user resume")
    assert tsm.state == TaskState.CANCELLED
    assert ctx1.closed.is_set() and not ctx1.is_current()  # 旧ストリーム明示クローズ
    assert flushed, "キューフラッシュフックが呼ばれていない"
    assert default_loop_guard.get_history() == [], "再開時に LoopGuard 履歴がクリアされていない"

    ctx2 = tsm.begin_turn(steering=True)  # 再バインド
    assert tsm.state == TaskState.RUNNING and ctx2.is_current() and not ctx1.is_current()
    # 旧ストリームの後始末が新ターンの状態を壊さない
    tsm.end_turn(ctx1)
    assert tsm.state == TaskState.RUNNING
    tsm.end_turn(ctx2)
    assert tsm.state == TaskState.IDLE


def test_guarded_call_never_raises():
    def boom():
        raise sqlite3.OperationalError("database is locked")

    res = guarded_call("memory", boom)
    assert res["ok"] is False and "database is locked" in res["error"] and res["hint"]
    assert guarded_call("ok", lambda: 42)["result"] == 42


# ───────────────────────── 4. LoopGuard ─────────────────────────
def test_loop_guard_normalizes_volatile_args():
    assert normalize_args_repr("run at 2026-11-05T22:35:37Z id=1730846137123") == \
        normalize_args_repr("run at 2026-11-05T22:36:01Z id=1730846199999")

    lg = LoopGuard(threshold=3)
    assert not lg.record_call("fetch", '{"url": "x", "ts": "2026-11-05T22:35:37Z"}')
    assert not lg.record_call("fetch", '{"url": "x", "ts": "2026-11-05T22:35:38Z"}')
    assert lg.record_call("fetch", '{"url": "x", "ts": "2026-11-05T22:35:39Z"}'), "タイムスタンプ差で回避された"


def test_loop_guard_similarity_and_cycle_and_no_false_positive():
    lg = LoopGuard(threshold=3)
    base = "grep -rn 'def process_request' /data/data/com.termux/files/home/TUGUMIv6/core --include=*.py"
    assert not lg.record_call("sh", base + " #1")
    assert not lg.record_call("sh", base + " #2")
    assert lg.record_call("sh", base + " #3"), "高類似引数の実質ループを検知できない"

    lg = LoopGuard(threshold=3)
    seq = [("a", "1"), ("b", "2"), ("c", "3")] * 3
    results = [lg.record_call(n, a) for n, a in seq]
    assert results[-1] is True and not any(results[:-1]), "周期3ループの検知に失敗"

    lg = LoopGuard(threshold=3)
    assert not any(lg.record_call("x", str(i)) for i in range(10)), "短い異なる引数を誤検知"


def test_loop_guard_reset_on_resume_and_async_decorator():
    lg = LoopGuard(threshold=3)
    lg.record_call("t", "same")
    lg.record_call("t", "same")
    lg.mark_resumed()
    assert lg.record_call("t", "same") is False  # 再開直後のリトライを無限ループと誤認しない

    calls = []

    @lg.guard
    async def atool(x):
        calls.append(x)
        return "ok"

    lg.reset()
    assert asyncio.run(atool(1)) == "ok"
    assert asyncio.run(atool(1)) == "ok"
    blocked = json.loads(asyncio.run(atool(1)))
    assert blocked["loop_blocked"] is True and len(calls) == 2


# ───────────────────────── 5. SQLite / RAG ─────────────────────────
def test_sqlite_concurrent_writes_no_lock_error(tmp_path):
    mem = SQLiteMemory(db_path=str(tmp_path / "m.db"))
    errors = []

    def worker(i):
        try:
            for j in range(15):
                mem.add_message("user", f"msg {i}-{j}", session_id=f"s{i % 3}")
                mem.add_memory("fact", f"subj{i}-{j % 4}", f"content {j}")
        except Exception as e:  # noqa: BLE001
            errors.append(repr(e))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=60)
    assert not errors, errors[:3]
    assert len(mem.get_session_messages("s0", limit=500)) > 0


def test_sqlite_interrupted_transaction_leaves_no_lock(tmp_path):
    mem = SQLiteMemory(db_path=str(tmp_path / "m.db"))
    with pytest.raises(RuntimeError):
        with mem._get_connection() as conn:
            conn.execute("BEGIN IMMEDIATE")
            conn.execute("INSERT INTO chat_sessions (id, title) VALUES ('zz', 'interrupted')")
            raise RuntimeError("cancelled mid-write")  # CancelledError 相当の中断
    t0 = time.time()
    mem.add_message("user", "after resume", session_id="zz2")  # ロック残留があれば60秒待たされる
    assert time.time() - t0 < 3
    assert not any(s["id"] == "zz" for s in mem.get_sessions()), "中断された書込が rollback されていない"
    with pytest.raises(sqlite3.ProgrammingError):  # 接続が確実に close されている
        conn.execute("SELECT 1")


class _FailingEmbedClient:
    def embed_texts_batch(self, texts, batch_size=20):
        return [[0.1] * 4 for _ in texts]


def test_rag_add_knowledge_is_atomic_when_db_write_fails(tmp_path):
    """DB(FTS5)書込失敗・中断時に vector_store へ孤立ベクトルを残さない（Transactional Outbox）"""
    import memory.rag_engine as rag_mod

    rag = RAGEngine(
        gemini_client=_FailingEmbedClient(),
        rag_dirs=[str(tmp_path / "rag")],
        vector_cache_path=str(tmp_path / "cache.json"),
        db_path=str(tmp_path / "rag.db"),
    )
    probe = "/data/data/com.termux/files/home/TUGUMIv6/data/rag_knowledge/pytest_atomic_probe.md"
    before = list(rag.vector_store)

    def locked(*a, **k):
        raise sqlite3.OperationalError("database is locked")

    try:
        with pytest.MonkeyPatch.context() as m:
            m.setattr(rag_mod, "open_wal_connection", locked)
            assert rag.add_knowledge("pytest_atomic_probe", "テスト本文 " * 50, category="pytest") is False
        assert rag.vector_store == before
        assert not os.path.exists(str(tmp_path / "cache.json")), "失敗時にキャッシュJSONが更新された"

        assert rag.add_knowledge("pytest_atomic_probe", "テスト本文 " * 50, category="pytest") is True
        assert rag.vector_store and all(it["file_path"] == probe for it in rag.vector_store)
    finally:
        if os.path.exists(probe):
            os.remove(probe)


def test_rag_cache_atomic_save_and_outbox_recovery(tmp_path):
    cache = tmp_path / "cache.json"
    kwargs = dict(gemini_client=None, rag_dirs=[str(tmp_path / "rag")], vector_cache_path=str(cache), db_path=str(tmp_path / "rag.db"))
    rag = RAGEngine(**kwargs)
    rag.vector_store = [{"source_chunk_id": "a#0", "file_path": "/x/a.md", "rel_path": "a.md", "folder": "t",
                         "title": "A", "text": "outbox recovery keyword", "embedding": []}]
    rag._save_vector_cache()
    assert json.loads(cache.read_text(encoding="utf-8"))[0]["title"] == "A"
    assert not os.path.exists(str(cache) + ".tmp")

    # vector_store 更新後・FTS5同期前に中断された状態を再現（マーカーだけ残る）
    rag._mark_outbox_dirty()
    rag2 = RAGEngine(**kwargs)  # 再起動 → Outbox 回復で FTS5 が再構築される
    assert not os.path.exists(rag2._outbox_path)
    with sqlite3.connect(kwargs["db_path"]) as conn:
        n = conn.execute("SELECT count(*) FROM knowledge_fts WHERE content LIKE '%outbox recovery%'").fetchone()[0]
    assert n == 1


# ───────────────────────── 6. Verifier Fail-Closed ─────────────────────────
def test_verifier_fail_closed_on_unexpected_exception(tmp_path, monkeypatch):
    target = tmp_path / "ok.py"
    target.write_text("x = 1\n", encoding="utf-8")
    v = SystemVerifier(workspace_root=str(tmp_path))

    def boom(_):
        raise RuntimeError("verifier internals exploded")

    monkeypatch.setattr(v, "check_syntax", boom)
    with pytest.raises(SecurityVerificationFailure) as ei:
        v.verify_all_gates(str(target))
    assert ei.value.result["passed"] is False

    # ゲート単体の内部例外でも valid=False（通過させない）
    v2 = SystemVerifier(workspace_root=str(tmp_path))
    monkeypatch.setattr(v2, "_check_syntax_impl", boom)
    assert v2.check_syntax(str(target))["valid"] is False

    # 回帰スイート不在は fail-closed では「検証不能=拒絶」
    ok, _ = SystemVerifier(workspace_root=str(tmp_path)).run_regression_gate(test_target=str(tmp_path / "nope.py"))
    assert ok is False


# ───────────────────────── 7. ContextCompressor Pinned ─────────────────────────
def test_context_compressor_pins_soul_and_system_messages():
    cc = ContextCompressor()
    soul = cc.get_pinned_context()
    assert soul, "SOUL.md が読み込めない"
    msgs = [{"role": "system", "content": "GUARDRAIL"}, {"role": "assistant", "content": soul}]
    msgs += [{"role": "user" if i % 2 == 0 else "assistant", "content": f"m{i}"} for i in range(40)]
    pruned = cc.prune_history(msgs, max_turns=6)
    assert pruned[0]["content"] == "GUARDRAIL"
    assert any(m["content"] == soul for m in pruned), "SOUL.md が剪定で脱落した"
    assert len([m for m in pruned if m["content"].startswith("m")]) == 6
    assert cc.mask_observation(soul + "\n" + "\n".join(["l"] * 400)) .count("Observation Masked") == 0
    assert cc.protect_system_prompt("custom").startswith("[PINNED:SOUL]")
