from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session as DbSession

from app import docker_manager as dm
from app import pylabs_bridge as pb
from app.db import get_db
from app.deps import get_current_user
from app.models import LabSession, TaskProgress, User
from app.schemas import CheckResponse, CheckResult, SelectResponse

router = APIRouter(prefix="/api/tasks", tags=["tasks"])

PHASE_NAMES = {1: "Foundations", 2: "Idiomatic Python", 3: "Structure", 4: "Ecosystem", 5: "The Stack"}


def _progress_map(db: DbSession, user_id: int) -> dict[str, str]:
    rows = db.query(TaskProgress).filter(TaskProgress.user_id == user_id).all()
    return {r.task_id: r.status for r in rows}


def _set_status(db: DbSession, user_id: int, task_id: str, status_value: str) -> None:
    row = (
        db.query(TaskProgress)
        .filter(TaskProgress.user_id == user_id, TaskProgress.task_id == task_id)
        .first()
    )
    if row is None:
        row = TaskProgress(user_id=user_id, task_id=task_id, status=status_value)
        db.add(row)
    else:
        row.status = status_value
    db.commit()


def _task_summary(task, status_value: str) -> dict:
    return {
        "id": task.id,
        "phase": task.phase,
        "phaseName": PHASE_NAMES.get(task.phase, f"Phase {task.phase}"),
        "title": task.title,
        "difficulty": task.difficulty,
        "concepts": task.concepts,
        "index": pb.task_index(task),
        "isTerminalOnly": len(task.files) == 0,
        "status": status_value,
    }


@router.get("")
def list_tasks(user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    progress = _progress_map(db, user.id)
    tasks = [_task_summary(t, progress.get(t.id, "not_started")) for t in pb.ALL_TASKS]
    done = sum(1 for t in tasks if t["status"] == "passed")
    return {
        "tasks": tasks,
        "total": pb.total_tasks(),
        "completed": done,
        "currentTaskId": next((tid for tid, s in progress.items() if s == "current"), None),
    }


@router.get("/{task_id}")
def get_task(task_id: str, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    task = pb.get_task(task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"no such task: {task_id}")
    progress = _progress_map(db, user.id)
    ws_dir = pb.workspace_dir_for(user.id)
    editor_files = sorted(task.files.keys())
    return {
        **_task_summary(task, progress.get(task.id, "not_started")),
        "brief": task.brief,
        "hint": task.hint,
        "editorFiles": editor_files,
        "starterFiles": task.files,
        "workspaceHasFiles": any((ws_dir / f).exists() for f in editor_files),
    }


@router.post("/{task_id}/select", response_model=SelectResponse)
def select_task(task_id: str, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    task = pb.get_task(task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"no such task: {task_id}")

    # only one task is "current" at a time
    for row in db.query(TaskProgress).filter(
        TaskProgress.user_id == user.id, TaskProgress.status == "current"
    ):
        row.status = "not_started"
    db.commit()

    ws_dir = pb.workspace_dir_for(user.id)
    created = pb.materialize_starter_files(task, ws_dir)
    # in case a lab session container is already running: newly-materialised
    # files are owned by this (backend) process, not code-server's fixed
    # user, so without this a mid-session task switch would hand the
    # learner an unwritable starter file
    dm.sync_workspace_ownership(ws_dir)

    existing = _progress_map(db, user.id).get(task_id, "not_started")
    if existing != "passed":
        _set_status(db, user.id, task_id, "current")

    return SelectResponse(created_files=created)


@router.post("/{task_id}/check", response_model=CheckResponse)
def check_task(task_id: str, user: User = Depends(get_current_user), db: DbSession = Depends(get_db)):
    task = pb.get_task(task_id)
    if task is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, f"no such task: {task_id}")

    # Phase 2: if a lab session container is running, that's the real
    # source of truth — check inside it via `docker exec` (it sees exactly
    # what's on disk in the learner's actual VS Code). Otherwise fall back
    # to the in-process check against the same workspace dir (Phase 0/1
    # behaviour), so Check still works without starting a lab session.
    active_session = (
        db.query(LabSession)
        .filter(LabSession.user_id == user.id, LabSession.status == "running")
        .first()
    )
    if active_session is not None and dm.container_running(active_session.container_id):
        try:
            outcome = dm.run_check(active_session.container_id, task_id)
        except dm.LabError as e:
            raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, str(e))
        passed, results = outcome["passed"], outcome["results"]
    else:
        ws_dir = pb.workspace_dir_for(user.id)
        passed, results = pb.run_checks(task, ws_dir)

    if passed:
        _set_status(db, user.id, task_id, "passed")

    return CheckResponse(passed=passed, results=[CheckResult(**r) for r in results])
