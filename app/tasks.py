"""Collaborative task API, authorization, audit history, and deadline notices."""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field, ConfigDict, field_validator
from sqlalchemy import or_, select, func
from sqlalchemy.orm.exc import StaleDataError

from .auth import Principal, authenticate_token
from .models import (SessionLocal, User, Task, TaskAssignment, TaskComment,
                    TaskActivity, TaskNotification, Notification)

router = APIRouter(prefix="/api/v1/tasks", tags=["tasks"])
STATUSES = {"todo", "in_progress", "on_hold", "completed", "cancelled"}
PRIORITIES = {"low", "medium", "high", "urgent"}


class TaskInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=20000)
    assignee_ids: list[int] = Field(default_factory=list, max_length=50)
    priority: str = "medium"
    status: str = "todo"
    due_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def nonblank_title(cls, value):
        value = value.strip()
        if not value: raise ValueError("Title is required")
        return value


class TaskPatch(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=20000)
    assignee_ids: list[int] | None = Field(default=None, max_length=50)
    priority: str | None = None
    status: str | None = None
    due_at: datetime | None = None

    @field_validator("title")
    @classmethod
    def nonblank_optional_title(cls, value):
        if value is None: raise ValueError("Title cannot be null")
        value = value.strip()
        if not value: raise ValueError("Title is required")
        return value


class CommentInput(BaseModel):
    body: str = Field(min_length=1, max_length=10000)

    @field_validator("body")
    @classmethod
    def nonblank_body(cls, value):
        value = value.strip()
        if not value: raise ValueError("Comment cannot be empty")
        return value


class AssignmentInput(BaseModel):
    assignee_ids: list[int] = Field(max_length=50)


class StatusInput(BaseModel):
    status: str


def _db_user(db, principal):
    user = db.get(User, principal.id) if principal.id else db.scalar(select(User).where(User.username == principal.username))
    if not user or not user.is_active:
        raise HTTPException(403, "A registered active user is required")
    return user


def _accessible(db, task, user):
    return user.role == "admin" or task.creator_id == user.id or db.scalar(
        select(TaskAssignment.id).where(TaskAssignment.task_id == task.id,
                                        TaskAssignment.user_id == user.id,
                                        TaskAssignment.ended_at.is_(None)).limit(1)
    ) is not None


def _require_task(db, task_id, user):
    task = db.get(Task, task_id)
    if not task or not _accessible(db, task, user):
        raise HTTPException(404, "Task not found")
    return task


def _activity(db, task, user, action, detail=""):
    db.add(TaskActivity(task_id=task.id, user_id=user.id, username=user.username, action=action, detail=detail))


def _notify(db, task, user_id, event, title, message, severity="info"):
    if not user_id or (user_id == task.creator_id and event.startswith("assign:")):
        return
    exists = db.scalar(select(TaskNotification.id).where(TaskNotification.task_id == task.id,
        TaskNotification.user_id == user_id, TaskNotification.event == event))
    if exists:
        return
    user = db.get(User, user_id)
    if not user or not user.is_active:
        return
    db.add(TaskNotification(task_id=task.id, user_id=user_id, event=event))
    db.add(Notification(source="watchtower", recipient=user.username, title=title,
        message=message, status="new", severity=severity, requires_approval=False,
        approval_status="not_required", metadata_json='{}', task_id=str(task.id),
        task_name=task.title, created_at=datetime.utcnow(), updated_at=datetime.utcnow()))


def _assignees(db, task_id, active_only=False):
    stmt = select(User).join(TaskAssignment, TaskAssignment.user_id == User.id).where(
        TaskAssignment.task_id == task_id, TaskAssignment.ended_at.is_(None))
    if active_only:
        stmt = stmt.where(User.is_active.is_(True))
    return db.scalars(stmt.order_by(User.username)).all()


def _serialize(db, task):
    creator = db.get(User, task.creator_id) if task.creator_id else None
    assignments = db.scalars(select(TaskAssignment).where(TaskAssignment.task_id == task.id).order_by(TaskAssignment.assigned_at)).all()
    return {"id": task.id, "title": task.title, "description": task.description,
        "creator": {"id": creator.id, "username": creator.username} if creator else {"id": None, "username": task.creator_name},
        "assignees": [{"id": u.id, "username": u.username} for u in _assignees(db, task.id, True)],
        "assignment_history": [{"user_id": a.user_id, "username": a.username, "assigned_by": a.assigned_by, "assigned_by_name": a.assigned_by_name,
          "assigned_at": a.assigned_at, "ended_at": a.ended_at} for a in assignments],
        "priority": task.priority, "status": task.status, "due_at": task.due_at,
        "completed_at": task.completed_at, "created_at": task.created_at, "updated_at": task.updated_at}


def _normalize_due(value):
    if value is None: return None
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value


def _set_assignees(db, task, user, ids):
    ids = list(dict.fromkeys(ids or []))
    users = db.scalars(select(User).where(User.id.in_(ids), User.is_active.is_(True))).all() if ids else []
    if len(users) != len(ids): raise HTTPException(422, "Assignees must be active WatchTower users")
    current = {a.user_id: a for a in db.scalars(select(TaskAssignment).where(TaskAssignment.task_id == task.id, TaskAssignment.ended_at.is_(None))).all()}
    wanted = set(ids)
    changed = current.keys() != wanted
    for uid, assignment in current.items():
        if uid not in wanted:
            assignment.ended_at = datetime.utcnow()
            old_user = db.get(User, uid) if uid else None
            _activity(db, task, user, "unassigned", f"Removed {old_user.username if old_user else assignment.username}")
    for assignee in users:
        if assignee.id not in current:
            assignment = TaskAssignment(task_id=task.id, user_id=assignee.id, username=assignee.username,
                                        assigned_by=user.id, assigned_by_name=user.username)
            db.add(assignment); db.flush()
            _activity(db, task, user, "assigned", f"Assigned {assignee.username}")
            _notify(db, task, assignee.id, f"assign:{assignment.id}", "New task assigned", task.title)
    return changed


@router.get("")
def list_tasks(principal: Principal = Depends(authenticate_token), view: str = "all",
               q: str | None = None, status: str | None = None, priority: str | None = None,
               assignee_id: int | None = None, creator_id: int | None = None,
               due: str | None = None, sort: str = "created_at", direction: str = "desc",
               limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    db = SessionLocal()
    try:
        user = _db_user(db, principal)
        if status and status not in STATUSES: raise HTTPException(422, "Invalid task status")
        if priority and priority not in PRIORITIES: raise HTTPException(422, "Invalid task priority")
        if due not in {None, "upcoming", "overdue"}: raise HTTPException(422, "Invalid deadline filter")
        if view not in {"all", "my", "assigned_by_me", "completed", "overdue"}: raise HTTPException(422, "Invalid task view")
        if sort not in {"created_at", "updated_at", "due_at", "priority", "status", "title"}: raise HTTPException(422, "Invalid sort field")
        if direction not in {"asc", "desc"}: raise HTTPException(422, "Invalid sort direction")
        stmt = select(Task)
        access = [Task.creator_id == user.id, Task.id.in_(select(TaskAssignment.task_id).where(TaskAssignment.user_id == user.id, TaskAssignment.ended_at.is_(None)))]
        if user.role != "admin": stmt = stmt.where(or_(*access))
        if view == "my": stmt = stmt.where(Task.id.in_(select(TaskAssignment.task_id).where(TaskAssignment.user_id == user.id, TaskAssignment.ended_at.is_(None))))
        elif view == "assigned_by_me": stmt = stmt.where(Task.creator_id == user.id)
        elif view == "completed": stmt = stmt.where(Task.status == "completed")
        elif view == "overdue": stmt = stmt.where(Task.due_at < datetime.utcnow(), Task.status.not_in(["completed", "cancelled"]))
        if status: stmt = stmt.where(Task.status == status)
        if priority: stmt = stmt.where(Task.priority == priority)
        if q: stmt = stmt.where(or_(Task.title.ilike(f"%{q.strip()}%"), Task.description.ilike(f"%{q.strip()}%")))
        if assignee_id: stmt = stmt.where(Task.id.in_(select(TaskAssignment.task_id).where(TaskAssignment.user_id == assignee_id, TaskAssignment.ended_at.is_(None))))
        if creator_id: stmt = stmt.where(Task.creator_id == creator_id)
        if due == "upcoming": stmt = stmt.where(Task.due_at >= datetime.utcnow())
        if due == "overdue": stmt = stmt.where(Task.due_at < datetime.utcnow())
        sort_col = getattr(Task, sort, Task.created_at)
        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = db.scalars(stmt.order_by(sort_col.asc() if direction == "asc" else sort_col.desc()).offset(offset).limit(limit)).all()
        return {"items": [_serialize(db, t) for t in rows], "total": total, "limit": limit, "offset": offset}
    finally: db.close()


@router.get("/summary")
def task_summary(principal: Principal = Depends(authenticate_token)):
    db = SessionLocal()
    try:
        user = _db_user(db, principal)
        scope = [] if user.role == "admin" else [or_(Task.creator_id == user.id, Task.id.in_(select(TaskAssignment.task_id).where(TaskAssignment.user_id == user.id, TaskAssignment.ended_at.is_(None))))]
        def count(*conditions):
            return db.scalar(select(func.count(Task.id)).where(*scope, *conditions)) or 0
        return {"active": count(Task.status.not_in(["completed", "cancelled"])),
            "my_pending": count(Task.id.in_(select(TaskAssignment.task_id).where(TaskAssignment.user_id == user.id, TaskAssignment.ended_at.is_(None))), Task.status.not_in(["completed", "cancelled"])),
            "in_progress": count(Task.status == "in_progress"),
            "overdue": count(Task.due_at < datetime.utcnow(), Task.status.not_in(["completed", "cancelled"])),
            "completed": count(Task.status == "completed"), "total": count()}
    finally: db.close()


@router.get("/users")
def task_users(principal: Principal = Depends(authenticate_token)):
    db = SessionLocal()
    try:
        _db_user(db, principal)
        return [{"id": u.id, "username": u.username} for u in db.scalars(select(User).where(User.is_active.is_(True)).order_by(User.username)).all()]
    finally: db.close()


@router.post("", status_code=201)
def create_task(payload: TaskInput, principal: Principal = Depends(authenticate_token)):
    if payload.priority not in PRIORITIES or payload.status not in STATUSES: raise HTTPException(422, "Invalid priority or status")
    db = SessionLocal()
    try:
        user = _db_user(db, principal)
        task = Task(title=payload.title.strip(), description=payload.description, creator_id=user.id, creator_name=user.username,
            priority=payload.priority, status=payload.status, due_at=_normalize_due(payload.due_at),
            completed_at=datetime.utcnow() if payload.status == "completed" else None)
        db.add(task); db.flush(); _activity(db, task, user, "created", "Task created")
        _set_assignees(db, task, user, payload.assignee_ids)
        db.commit(); db.refresh(task); return _serialize(db, task)
    except StaleDataError:
        db.rollback(); raise HTTPException(409, "Task changed concurrently. Reload it and retry.")
    except Exception: db.rollback(); raise
    finally: db.close()


@router.get("/{task_id}")
def get_task(task_id: int, principal: Principal = Depends(authenticate_token)):
    db = SessionLocal()
    try:
        user = _db_user(db, principal); task = _require_task(db, task_id, user)
        comments = db.scalars(select(TaskComment).where(TaskComment.task_id == task_id).order_by(TaskComment.created_at)).all()
        history = db.scalars(select(TaskActivity).where(TaskActivity.task_id == task_id).order_by(TaskActivity.created_at)).all()
        result = _serialize(db, task)
        result["comments"] = [{"user": db.get(User, c.user_id).username if c.user_id else c.username, "body": c.body, "created_at": c.created_at} for c in comments]
        result["activity"] = [{"user": db.get(User, a.user_id).username if a.user_id else a.username, "action": a.action, "detail": a.detail, "created_at": a.created_at} for a in history]
        result["can_edit"] = user.role == "admin" or task.creator_id == user.id
        return result
    finally: db.close()


@router.post("/{task_id}/assign")
def assign_task(task_id: int, payload: AssignmentInput, principal: Principal = Depends(authenticate_token)):
    # Kept as a dedicated endpoint for API clients that only manage assignments.
    ids = payload.assignee_ids
    db = SessionLocal()
    try:
        user = _db_user(db, principal); task = _require_task(db, task_id, user)
        if user.role != "admin" and task.creator_id != user.id: raise HTTPException(403, "Only the creator or an administrator can reassign this task")
        _set_assignees(db, task, user, ids); task.updated_at = datetime.utcnow(); db.commit()
        return _serialize(db, task)
    except Exception: db.rollback(); raise
    finally: db.close()


@router.post("/{task_id}/status")
def set_task_status(task_id: int, payload: StatusInput, principal: Principal = Depends(authenticate_token)):
    status_value = payload.status
    if status_value not in STATUSES: raise HTTPException(422, "Invalid task status")
    return update_task(task_id, TaskPatch(status=status_value), principal)


@router.patch("/{task_id}")
def update_task(task_id: int, payload: TaskPatch, principal: Principal = Depends(authenticate_token)):
    db = SessionLocal()
    try:
        user = _db_user(db, principal); task = _require_task(db, task_id, user)
        data = payload.model_dump(exclude_unset=True)
        if any(field in data and data[field] is None for field in ("description", "assignee_ids", "priority", "status")):
            raise HTTPException(422, "Task fields cannot be null")
        is_assigned = db.scalar(select(TaskAssignment.id).where(TaskAssignment.task_id == task.id, TaskAssignment.user_id == user.id, TaskAssignment.ended_at.is_(None))) is not None
        full_edit = user.role == "admin" or task.creator_id == user.id
        if not full_edit and not (is_assigned and set(data) <= {"status"}): raise HTTPException(403, "You cannot edit this task")
        for field, value in data.items():
            if field == "assignee_ids": _set_assignees(db, task, user, value)
            elif field == "status":
                if value not in STATUSES: raise HTTPException(422, "Invalid task status")
                if task.status != value:
                    old = task.status; task.status = value; _activity(db, task, user, "status", f"{old} → {value}")
                    task.completed_at = datetime.utcnow() if value == "completed" else None
                    if value == "completed": _notify(db, task, task.creator_id, "completed", "Task completed", task.title)
            elif field == "priority":
                if value not in PRIORITIES: raise HTTPException(422, "Invalid task priority")
                if task.priority != value: _activity(db, task, user, "priority", f"{task.priority} → {value}"); task.priority = value
            elif field == "due_at":
                value = _normalize_due(value)
                if task.due_at != value: _activity(db, task, user, "deadline", "Deadline changed"); task.due_at = value
            else: setattr(task, field, value.strip() if field == "title" else value)
        task.updated_at = datetime.utcnow(); db.commit(); db.refresh(task); return _serialize(db, task)
    except StaleDataError:
        db.rollback(); raise HTTPException(409, "Task changed concurrently. Reload it and retry.")
    except Exception: db.rollback(); raise
    finally: db.close()


@router.delete("/{task_id}", status_code=204)
def delete_task(task_id: int, principal: Principal = Depends(authenticate_token)):
    db = SessionLocal()
    try:
        user = _db_user(db, principal); task = _require_task(db, task_id, user)
        if user.role != "admin" and task.creator_id != user.id: raise HTTPException(403, "Only the creator or an administrator can delete this task")
        db.delete(task); db.commit()
    finally: db.close()


@router.post("/{task_id}/comments", status_code=201)
def add_comment(task_id: int, payload: CommentInput, principal: Principal = Depends(authenticate_token)):
    db = SessionLocal()
    try:
        user = _db_user(db, principal); task = _require_task(db, task_id, user)
        comment = TaskComment(task_id=task.id, user_id=user.id, username=user.username, body=payload.body.strip()); db.add(comment)
        _activity(db, task, user, "comment", payload.body.strip())
        for assignee in _assignees(db, task.id, True):
            if assignee.id != user.id: _notify(db, task, assignee.id, f"comment:{comment.id}", "New task comment", f"{user.username}: {payload.body.strip()[:180]}")
        db.commit(); return {"id": comment.id, "body": comment.body, "created_at": comment.created_at}
    except Exception: db.rollback(); raise
    finally: db.close()


def check_task_deadlines():
    """Idempotent deadline sweep; APScheduler runs it after every restart."""
    db = SessionLocal(); now = datetime.utcnow()
    try:
        tasks = db.scalars(select(Task).where(Task.due_at.is_not(None), Task.status.not_in(["completed", "cancelled"]))).all()
        for task in tasks:
            for assignee in _assignees(db, task.id, True):
                if now <= task.due_at <= now + timedelta(hours=24):
                    _notify(db, task, assignee.id, f"soon:{task.due_at:%Y%m%d%H%M}", "Task due within 24 hours", task.title, "warning")
                elif task.due_at < now:
                    _notify(db, task, assignee.id, f"late:{task.due_at:%Y%m%d%H%M}", "Task overdue", task.title, "error")
        db.commit()
    except Exception: db.rollback(); raise
    finally: db.close()
