"""Tests for Celery scheduler safeguards."""

from __future__ import annotations

import asyncio
from types import SimpleNamespace
from uuid import uuid4

import pytest
from celery.exceptions import Ignore

from app.scheduler.tasks import RunPlaybookTask, enqueue_run_playbook


def test_enqueue_run_playbook_uses_queue_metrics(monkeypatch):
    calls = []

    def fake_apply_async(args, ignore_result):
        calls.append((args, ignore_result))

    monkeypatch.setattr("app.scheduler.tasks.run_playbook_task.apply_async", fake_apply_async)

    enqueue_run_playbook("playbook", None, source="api")

    assert calls == [(("playbook", None), True)]


def test_run_task_duplicate_lock(monkeypatch):
    lock_calls = SimpleNamespace(count=0)

    async def fake_acquire(name):
        lock_calls.count += 1
        return lock_calls.count == 1

    async def fake_release(name):
        return None

    async def fake_run_playbook(playbook_id, schedule_id):
        return {"matched": 0}

    monkeypatch.setattr("app.scheduler.tasks.acquire_lock_async", fake_acquire)
    monkeypatch.setattr("app.scheduler.tasks.release_lock_async", fake_release)
    monkeypatch.setattr("app.scheduler.tasks._run_playbook", fake_run_playbook)

    task = RunPlaybookTask()

    task.run(str(uuid4()), None)

    with pytest.raises(Ignore):
        task.run(str(uuid4()), None)


def test_run_task_retry_exhaustion(monkeypatch):
    attempts = []

    async def fake_acquire(name):
        return True

    async def fake_release(name):
        return None

    def fake_run_async(playbook_id, schedule_id):
        attempts.append(1)
        raise RuntimeError("boom")

    monkeypatch.setattr("app.scheduler.tasks.acquire_lock_async", fake_acquire)
    monkeypatch.setattr("app.scheduler.tasks.release_lock_async", fake_release)
    monkeypatch.setattr("app.scheduler.tasks._run_async", fake_run_async)

    task = RunPlaybookTask()
    with pytest.raises(RuntimeError):
        task.run(str(uuid4()), None)

    assert len(attempts) == 1
