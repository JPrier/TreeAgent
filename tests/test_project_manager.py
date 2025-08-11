import time

from src.dataModel import Task, TaskType
from src.dataModel.project import Project
from src.dataManagement.project_manager import (
    save_project_state,
    load_project_state,
    latest_snapshot_path,
)


def build_project() -> Project:
    root = Task(id="root", description="d", type=TaskType.HLD)
    fail1 = Task(id="f1", description="f1", type=TaskType.REQUIREMENTS)
    fail2 = Task(id="f2", description="f2", type=TaskType.RESEARCH)
    comp1 = Task(id="c1", description="c1", type=TaskType.IMPLEMENT)
    comp2 = Task(id="c2", description="c2", type=TaskType.IMPLEMENT)
    queue1 = Task(id="q1", description="q1", type=TaskType.REVIEW)
    queue2 = Task(id="q2", description="q2", type=TaskType.DEPLOY)
    return Project(
        rootTask=root,
        failedTasks=[fail1, fail2],
        completedTasks=[comp1, comp2],
        inProgressTasks=[],
        queuedTasks=[queue1, queue2],
    )


def build_project_with_inprogress() -> Project:
    proj = build_project()
    prog1 = Task(id="p1", description="p1", type=TaskType.LLD)
    prog2 = Task(id="p2", description="p2", type=TaskType.TEST)
    proj.inProgressTasks = [prog1, prog2]
    return proj


def build_empty_project() -> Project:
    root = Task(id="root", description="d", type=TaskType.HLD)
    return Project(
        rootTask=root,
        failedTasks=[],
        completedTasks=[],
        inProgressTasks=[],
        queuedTasks=[],
    )


def test_save_and_load_round_trip(tmp_path):
    project = build_project()
    snapshot = save_project_state(project, tmp_path)
    loaded = load_project_state(snapshot)
    assert loaded == project


def test_inprogress_requeued(tmp_path):
    project = build_project_with_inprogress()
    snapshot = save_project_state(project, tmp_path)
    loaded = load_project_state(snapshot)
    assert not loaded.inProgressTasks
    ids = [t.id for t in project.inProgressTasks]
    assert [t.id for t in loaded.queuedTasks[: len(ids)]] == ids


def test_empty_project(tmp_path):
    project = build_empty_project()
    snap = save_project_state(project, tmp_path)
    loaded = load_project_state(snap)
    assert loaded == project


def test_latest_snapshot_path(tmp_path):
    project = build_project()
    save_project_state(project, tmp_path)
    time.sleep(0.01)
    project.completedTasks.append(project.rootTask)
    snap2 = save_project_state(project, tmp_path)
    assert latest_snapshot_path(tmp_path) == snap2
