"""Small collaborative checklist API."""
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import func, or_, select
from sqlalchemy.orm.exc import StaleDataError

from .auth import Principal, authenticate_token
from .models import Notification, SessionLocal, Todo, User

router = APIRouter(prefix="/api/v1/todos", tags=["todos"])


class TodoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str = Field(min_length=1, max_length=200)
    description: str = Field(default="", max_length=12000)
    assigned_to_user_id: int | None = None
    due_date: datetime | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value):
        value = value.strip()
        if not value:
            raise ValueError("Title is required")
        return value


class TodoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    title: str | None = Field(default=None, min_length=1, max_length=200)
    description: str | None = Field(default=None, max_length=12000)
    assigned_to_user_id: int | None = None
    due_date: datetime | None = None
    is_completed: bool | None = None

    @field_validator("title")
    @classmethod
    def title_not_blank(cls, value):
        if value is None:
            raise ValueError("Title cannot be null")
        value = value.strip()
        if not value:
            raise ValueError("Title is required")
        return value


def _user(db, principal):
    user = db.get(User, principal.id) if principal.id else db.scalar(select(User).where(User.username == principal.username))
    if user is None or not user.is_active:
        raise HTTPException(403, "An active WatchTower account is required")
    return user


def _visible(db, todo, user):
    return user.role == "admin" or todo.created_by_user_id == user.id or todo.assigned_to_user_id == user.id


def _todo(db, todo_id, user):
    todo = db.get(Todo, todo_id)
    if todo is None or not _visible(db, todo, user):
        raise HTTPException(404, "To-do item not found")
    return todo


def _utc_naive(value):
    if value is None:
        return None
    return value.astimezone(timezone.utc).replace(tzinfo=None) if value.tzinfo else value


def _set_assignee(db, todo, actor, assignee_id):
    old_id = todo.assigned_to_user_id
    if old_id == assignee_id:
        return
    assignee = db.get(User, assignee_id) if assignee_id is not None else None
    if assignee_id is not None and (assignee is None or not assignee.is_active):
        raise HTTPException(422, "Assigned user must be an active WatchTower user")
    todo.assigned_to_user_id = assignee.id if assignee else None
    todo.assigned_to_name = assignee.username if assignee else None
    if assignee:
        title = "New Task Assigned" if old_id is None else "Task Reassigned To You"
        db.add(Notification(
            source="watchtower", recipient=assignee.username, title=title,
            message=f"You have been assigned a new task: {todo.title}.", status="new",
            severity="info", requires_approval=False, approval_status="not_required",
            metadata_json="{}", task_id=str(todo.id), task_name=todo.title,
            created_at=datetime.utcnow(), updated_at=datetime.utcnow(),
        ))


def _serialize(db, todo, user):
    creator = db.get(User, todo.created_by_user_id) if todo.created_by_user_id else None
    assignee = db.get(User, todo.assigned_to_user_id) if todo.assigned_to_user_id else None
    is_assignee = todo.assigned_to_user_id == user.id
    can_edit = user.role == "admin" or todo.created_by_user_id == user.id
    return {
        "id": todo.id, "title": todo.title, "description": todo.description,
        "created_by": {"id": creator.id, "username": creator.username} if creator else {"id": None, "username": todo.created_by_name},
        "assigned_to": {"id": assignee.id, "username": assignee.username} if assignee else (
            {"id": None, "username": todo.assigned_to_name} if todo.assigned_to_name else None),
        "assigned_to_user_id": todo.assigned_to_user_id,
        "due_date": todo.due_date, "is_completed": todo.is_completed,
        "created_at": todo.created_at, "updated_at": todo.updated_at,
        "completed_at": todo.completed_at, "can_edit": can_edit,
        "can_complete": user.role == "admin" or is_assignee,
        "can_delete": can_edit,
    }


def _visible_query(user):
    if user.role == "admin":
        return []
    return [or_(Todo.created_by_user_id == user.id, Todo.assigned_to_user_id == user.id)]


@router.get("")
def list_todos(principal: Principal = Depends(authenticate_token), view: str = "all",
               q: str | None = None, sort: str | None = None,
               limit: int = Query(50, ge=1, le=100), offset: int = Query(0, ge=0)):
    if view not in {"all", "my", "assigned_by_me", "pending", "completed"}:
        raise HTTPException(422, "Invalid to-do view")
    if sort not in {None, "due_date", "title", "created_at", "assignee"}:
        raise HTTPException(422, "Invalid to-do sort")
    db = SessionLocal()
    try:
        user = _user(db, principal)
        stmt = select(Todo).where(*_visible_query(user))
        if view == "my":
            stmt = stmt.where(Todo.assigned_to_user_id == user.id)
        elif view == "assigned_by_me":
            stmt = stmt.where(Todo.created_by_user_id == user.id)
        elif view == "completed":
            stmt = stmt.where(Todo.is_completed.is_(True))
        elif view == "pending":
            stmt = stmt.where(Todo.is_completed.is_(False))
        if q and q.strip():
            needle = f"%{q.strip()}%"
            stmt = stmt.where(or_(Todo.title.ilike(needle), Todo.description.ilike(needle)))
        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        ordering = {
            None: [Todo.is_completed.asc(), Todo.due_date.asc().nullslast(), Todo.created_at.desc()],
            "due_date": [Todo.due_date.asc().nullslast()],
            "title": [func.lower(Todo.title).asc()],
            "created_at": [Todo.created_at.desc()],
            "assignee": [func.lower(User.username).asc().nullslast()],
        }[sort]
        if sort == "assignee":
            stmt = stmt.outerjoin(User, Todo.assigned_to_user_id == User.id)
        rows = db.scalars(stmt.order_by(*ordering, Todo.id.desc())
                          .offset(offset).limit(limit)).all()
        return {"items": [_serialize(db, todo, user) for todo in rows], "total": total, "limit": limit, "offset": offset}
    finally:
        db.close()


@router.get("/summary")
def todo_summary(principal: Principal = Depends(authenticate_token)):
    db = SessionLocal()
    try:
        user = _user(db, principal)
        visible = _visible_query(user)
        count = lambda *filters: db.scalar(select(func.count(Todo.id)).where(*visible, *filters)) or 0
        return {
            "my_pending": count(Todo.assigned_to_user_id == user.id, Todo.is_completed.is_(False)),
            "assigned_by_me": count(Todo.created_by_user_id == user.id),
            "completed": count(Todo.is_completed.is_(True)),
            "my_total": count(Todo.assigned_to_user_id == user.id),
            "assigned_by_me_total": count(Todo.created_by_user_id == user.id),
            "total": count(),
        }
    finally:
        db.close()


@router.get("/assignees")
def list_assignees(principal: Principal = Depends(authenticate_token)):
    db = SessionLocal()
    try:
        _user(db, principal)
        return [{"id": row.id, "username": row.username} for row in db.scalars(
            select(User).where(User.is_active.is_(True)).order_by(User.username)).all()]
    finally:
        db.close()


@router.post("", status_code=201)
def create_todo(payload: TodoCreate, principal: Principal = Depends(authenticate_token)):
    db = SessionLocal()
    try:
        user = _user(db, principal)
        todo = Todo(title=payload.title, description=payload.description.strip(), created_by_user_id=user.id,
                    created_by_name=user.username, due_date=_utc_naive(payload.due_date))
        db.add(todo)
        db.flush()
        _set_assignee(db, todo, user, payload.assigned_to_user_id)
        db.commit()
        db.refresh(todo)
        return _serialize(db, todo, user)
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.get("/{todo_id}")
def get_todo(todo_id: int, principal: Principal = Depends(authenticate_token)):
    db = SessionLocal()
    try:
        user = _user(db, principal)
        return _serialize(db, _todo(db, todo_id, user), user)
    finally:
        db.close()


@router.patch("/{todo_id}")
def update_todo(todo_id: int, payload: TodoUpdate, principal: Principal = Depends(authenticate_token)):
    db = SessionLocal()
    try:
        user = _user(db, principal)
        todo = _todo(db, todo_id, user)
        changes = payload.model_dump(exclude_unset=True)
        full_edit = user.role == "admin" or todo.created_by_user_id == user.id
        is_assignee = todo.assigned_to_user_id == user.id
        if not full_edit and not (is_assignee and set(changes) <= {"is_completed"}):
            raise HTTPException(403, "You cannot edit this to-do item")
        if "is_completed" in changes and not (user.role == "admin" or is_assignee):
            raise HTTPException(403, "Only the assigned user or an administrator can complete this item")
        if any(key in changes and changes[key] is None for key in ("description",)):
            raise HTTPException(422, "Description cannot be null")
        for key, value in changes.items():
            if key == "assigned_to_user_id":
                _set_assignee(db, todo, user, value)
            elif key == "due_date":
                todo.due_date = _utc_naive(value)
            elif key == "is_completed":
                if not isinstance(value, bool):
                    raise HTTPException(422, "is_completed must be a boolean")
                if todo.is_completed != value:
                    todo.is_completed = value
                    todo.completed_at = datetime.utcnow() if value else None
            elif key == "title":
                todo.title = value
            else:
                todo.description = value.strip()
        todo.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(todo)
        return _serialize(db, todo, user)
    except StaleDataError:
        db.rollback()
        raise HTTPException(409, "This item changed while you were editing it. Reload and retry.")
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


@router.delete("/{todo_id}", status_code=204)
def delete_todo(todo_id: int, principal: Principal = Depends(authenticate_token)):
    db = SessionLocal()
    try:
        user = _user(db, principal)
        todo = _todo(db, todo_id, user)
        if user.role != "admin" and todo.created_by_user_id != user.id:
            raise HTTPException(403, "Only the creator or an administrator can delete this item")
        db.delete(todo)
        db.commit()
        return Response(status_code=204)
    finally:
        db.close()
