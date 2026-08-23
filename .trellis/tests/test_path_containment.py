from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_DIR = REPO_ROOT / ".trellis" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

from common.active_task import (  # noqa: E402
    ActiveTask,
    _active_from_ref,
    clear_active_task,
    resolve_active_task,
    resolve_task_ref,
)
from common.paths import (  # noqa: E402
    get_current_task,
    resolve_repo_path,
    resolve_task_ref as resolve_path_task_ref,
)
from common.task_context import _resolve_context_entry_path  # noqa: E402


def _make_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    (repo / ".trellis" / "tasks").mkdir(parents=True)
    return repo


def _load_hook(relative_path: str):
    hook_path = REPO_ROOT / relative_path
    module_name = "test_" + "_".join(hook_path.parts[-3:]).replace("-", "_").replace(".", "_")
    spec = importlib.util.spec_from_file_location(module_name, hook_path)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_task_refs_are_confined_to_trellis_tasks(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    missing = repo / ".trellis" / "tasks" / "missing"

    assert resolve_task_ref(".trellis/tasks/missing", repo) == missing
    assert resolve_path_task_ref(".trellis/tasks/missing", repo) == missing
    assert resolve_task_ref(str(tmp_path / "outside"), repo) is None
    assert resolve_path_task_ref(str(tmp_path / "outside"), repo) is None
    assert resolve_task_ref(".trellis/tasks/../../../outside", repo) is None
    assert resolve_path_task_ref(".trellis/tasks/../../../outside", repo) is None
    assert resolve_task_ref(".trellis/workflow.md", repo) is None

    outside = tmp_path / "outside-task"
    outside.mkdir()
    (repo / ".trellis" / "tasks" / "linked").symlink_to(outside, target_is_directory=True)
    assert resolve_task_ref(".trellis/tasks/linked", repo) is None


def test_symlinked_task_store_outside_repo_is_rejected(tmp_path: Path) -> None:
    repo = tmp_path / "repo"
    (repo / ".trellis").mkdir(parents=True)
    outside_tasks = tmp_path / "tasks"
    outside_tasks.mkdir()
    (repo / ".trellis" / "tasks").symlink_to(outside_tasks, target_is_directory=True)

    assert resolve_task_ref(".trellis/tasks/missing", repo) is None
    assert resolve_path_task_ref(".trellis/tasks/missing", repo) is None


def test_unsafe_stale_refs_are_neutralized_but_safe_missing_refs_are_reported(
    tmp_path: Path,
) -> None:
    repo = _make_repo(tmp_path)

    unsafe = _active_from_ref(str(tmp_path / "outside"), repo, "session", "unsafe")
    traversal = _active_from_ref("../../../outside", repo, "session", "traversal")
    safe_missing = _active_from_ref("missing", repo, "session", "missing")

    assert unsafe is not None and unsafe.stale and unsafe.task_path is None
    assert traversal is not None and traversal.stale and traversal.task_path is None
    assert safe_missing is not None and safe_missing.stale
    assert safe_missing.task_path == ".trellis/tasks/missing"


def test_finish_clears_an_unsafe_stale_session_without_reading_it(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    repo = _make_repo(tmp_path)
    sessions = repo / ".trellis" / ".runtime" / "sessions"
    sessions.mkdir(parents=True)
    session_file = sessions / "unsafe-test.json"
    session_file.write_text(
        json.dumps({"current_task": str(tmp_path / "outside")}),
        encoding="utf-8",
    )
    monkeypatch.setenv("TRELLIS_CONTEXT_ID", "unsafe-test")

    active = resolve_active_task(repo)
    assert active.stale and active.task_path is None
    assert get_current_task(repo) is None

    previous = clear_active_task(repo)
    assert previous.stale and previous.task_path is None
    assert not session_file.exists()


def test_context_entries_are_repo_relative_and_contained(tmp_path: Path) -> None:
    repo = _make_repo(tmp_path)
    docs = repo / "docs"
    docs.mkdir()
    safe = docs / "safe.md"
    safe.write_text("safe", encoding="utf-8")
    outside = tmp_path / "secret.md"
    outside.write_text("secret", encoding="utf-8")
    (docs / "linked.md").symlink_to(outside)

    assert resolve_repo_path("docs/safe.md", repo) == safe
    assert resolve_repo_path(str(safe), repo) is None
    assert resolve_repo_path("../secret.md", repo) is None
    assert resolve_repo_path("docs/linked.md", repo) is None
    assert resolve_repo_path(["docs/safe.md"], repo) is None  # type: ignore[arg-type]
    assert _resolve_context_entry_path("docs/safe.md", repo, None) == safe
    assert _resolve_context_entry_path("../secret.md", repo, None) is None


@pytest.mark.parametrize(
    "hook_path",
    [
        ".claude/hooks/inject-subagent-context.py",
        ".codex/hooks/inject-subagent-context.py",
    ],
)
def test_context_hooks_refuse_manifest_and_entry_escapes(
    tmp_path: Path, hook_path: str
) -> None:
    repo = _make_repo(tmp_path)
    docs = repo / "docs"
    docs.mkdir()
    (docs / "safe.md").write_text("safe", encoding="utf-8")
    outside = tmp_path / "secret.md"
    outside.write_text("secret", encoding="utf-8")
    manifest = repo / "context.jsonl"
    manifest.write_text(
        "\n".join(
            [
                json.dumps({"file": "docs/safe.md", "reason": "safe"}),
                json.dumps({"file": "../secret.md", "reason": "escape"}),
                json.dumps({"file": ["docs/safe.md"], "reason": "malformed"}),
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    hook = _load_hook(hook_path)
    limits = {"max_file_bytes": 32768, "max_artifact_bytes": 65536, "max_total_bytes": 131072}
    budget = hook._Budget(limits["max_total_bytes"])
    blocks = hook._materialize_jsonl_entries(str(repo), "context.jsonl", limits, budget)

    assert any("safe" in block for block in blocks)
    assert all("secret" not in block for block in blocks)
    assert hook._read_file_bytes(str(repo), str(repo / "docs" / "safe.md")) is None
    assert hook.read_jsonl_entries(str(repo), "../context.jsonl") == []


@pytest.mark.parametrize(
    "hook_path",
    [
        ".claude/hooks/session-start.py",
        ".codex/hooks/session-start.py",
    ],
)
def test_session_hooks_report_stale_without_resolving_task_files(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, hook_path: str
) -> None:
    repo = _make_repo(tmp_path)
    hook = _load_hook(hook_path)
    stale = ActiveTask(None, "session", "unsafe", stale=True)
    monkeypatch.setattr(hook, "_resolve_active_task", lambda *_args, **_kwargs: stale)
    monkeypatch.setattr(
        hook,
        "_resolve_task_dir",
        lambda *_args, **_kwargs: pytest.fail("stale task path was resolved"),
    )

    status = hook._get_task_status(repo / ".trellis", {})

    assert "STALE POINTER" in status
