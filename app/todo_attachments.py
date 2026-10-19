"""Private, bounded task attachments. No upload directory is mounted as static content."""
import re
import zipfile
from pathlib import Path
from uuid import uuid4

from fastapi import Depends, HTTPException, Request
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request as StarletteRequest
from starlette.responses import FileResponse
from sqlalchemy import func, select, update

from .auth import Principal, authenticate_token
from .config import settings
from .models import Todo, TodoAttachment, User

MIME = {
    "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
    "webp": "image/webp", "pdf": "application/pdf", "txt": "text/plain",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "zip": "application/zip",
}


def attachment_path(name):
    if not re.fullmatch(r"[a-f0-9]{32}", name):
        raise HTTPException(404, "Attachment not found")
    root = Path(settings.todo_attachment_dir).resolve()
    path = root / name
    if path.is_symlink():
        raise HTTPException(404, "Attachment not found")
    return path


def validate_content(path, extension):
    with path.open("rb") as source:
        head = source.read(16)
    valid = False
    if extension == "png":
        valid = head.startswith(b"\x89PNG\r\n\x1a\n")
    elif extension in {"jpg", "jpeg"}:
        valid = head.startswith(b"\xff\xd8\xff")
    elif extension == "webp":
        valid = head[:4] == b"RIFF" and head[8:12] == b"WEBP"
    elif extension == "pdf":
        valid = head.startswith(b"%PDF-")
    elif extension == "txt":
        try:
            text = path.read_text(encoding="utf-8")
            valid = "\x00" not in text
        except UnicodeError:
            pass
    elif extension in {"zip", "docx", "xlsx"}:
        try:
            with zipfile.ZipFile(path) as archive:
                names = set(archive.namelist())
                valid = extension == "zip" or (
                    "[Content_Types].xml" in names and
                    ("word/document.xml" if extension == "docx" else "xl/workbook.xml") in names)
        except (zipfile.BadZipFile, OSError):
            pass
    if not valid:
        raise HTTPException(415, "File contents do not match the supported file type")


def serialize(db, item, user, todo):
    uploader = db.get(User, item.uploaded_by_user_id) if item.uploaded_by_user_id else None
    return {
        "id": item.id, "task_id": item.task_id, "original_filename": item.original_filename,
        "file_size": item.file_size, "content_type": item.content_type,
        "uploaded_by_user_id": item.uploaded_by_user_id,
        "uploaded_by": uploader.username if uploader else "Deleted user",
        "created_at": item.created_at,
        "can_delete": user.role == "admin" or todo.created_by_user_id == user.id or item.uploaded_by_user_id == user.id,
    }


def register_routes(router):
    # Import here so tests and all routes share the existing session factory.
    from . import todos

    @router.get("/{todo_id}/attachments")
    def list_attachments(todo_id: int, principal: Principal = Depends(authenticate_token)):
        with todos.SessionLocal() as db:
            user = todos._user(db, principal)
            todo = todos._todo(db, todo_id, user)
            return [serialize(db, item, user, todo) for item in db.scalars(
                select(TodoAttachment).where(TodoAttachment.task_id == todo_id).order_by(TodoAttachment.id))]

    @router.post("/{todo_id}/attachments", status_code=201)
    async def upload(todo_id: int, request: Request, principal: Principal = Depends(authenticate_token)):
        # Check authorization before parsing/spooling any untrusted body.
        with todos.SessionLocal() as db:
            user = todos._user(db, principal)
            todos._todo(db, todo_id, user)
        # Bound the entire multipart request, including chunked bodies and headers.
        # The browser sends one file per request; API batches allow up to 40 MiB.
        bound = 2 * settings.todo_attachment_max_bytes + 65536
        received = 0
        async def receive():
            nonlocal received
            message = await request.receive()
            received += len(message.get("body", b""))
            if received > bound:
                from starlette.formparsers import MultiPartException
                raise MultiPartException("Upload batch exceeds size limit")
            return message
        bounded = StarletteRequest(request.scope, receive)
        paths = []
        try:
            async with bounded.form(max_files=settings.todo_attachment_max_count, max_fields=0) as form:
                files = form.getlist("files")
                if not files or any(not hasattr(file, "filename") for file in files):
                    raise HTTPException(422, "Provide one or more files using the files field")
                with todos.SessionLocal() as db:
                    user = todos._user(db, principal)
                    todo = todos._todo(db, todo_id, user)
                    # Serialize uploads/deletion on the parent row (SQLite write lock;
                    # row lock on other databases), so concurrent uploads cannot exceed quota.
                    db.execute(update(Todo).where(Todo.id == todo_id).values(version_id=Todo.version_id + 1))
                    db.refresh(todo)
                    todos._todo(db, todo_id, user)
                    count = db.scalar(select(func.count(TodoAttachment.id)).where(TodoAttachment.task_id == todo_id))
                    if count + len(files) > settings.todo_attachment_max_count:
                        raise HTTPException(422, "Maximum attachments per task exceeded")
                    results = []
                    allowed = set(settings.todo_attachment_extensions.lower().split(",")) & MIME.keys()
                    for file in files:
                        name = (file.filename or "").replace("\\", "/").split("/")[-1]
                        name = "".join(c for c in name if c.isprintable() and c not in '<>:"|?*').strip()[:240]
                        extension = name.rsplit(".", 1)[-1].lower()
                        if not name or extension not in allowed:
                            raise HTTPException(415, "Unsupported attachment type")
                        path = attachment_path(uuid4().hex)
                        path.parent.mkdir(parents=True, exist_ok=True, mode=0o700)
                        paths.append(path)
                        size = 0
                        with path.open("xb") as output:
                            path.chmod(0o600)
                            while chunk := await file.read(1024 * 1024):
                                size += len(chunk)
                                if size > settings.todo_attachment_max_bytes:
                                    raise HTTPException(413, "Attachment exceeds file size limit")
                                output.write(chunk)
                        if size == 0:
                            raise HTTPException(422, "Empty attachments are not supported")
                        validate_content(path, extension)
                        item = TodoAttachment(task_id=todo_id, original_filename=name,
                            stored_filename=path.name, file_size=size, content_type=MIME[extension],
                            uploaded_by_user_id=user.id)
                        db.add(item)
                        results.append(item)
                    db.flush()
                    result = [serialize(db, item, user, todo) for item in results]
                    db.commit()
                    paths.clear()
                    return result
        except StarletteHTTPException as exc:
            if exc.status_code == 400 and "size limit" in str(exc.detail):
                raise HTTPException(413, "Upload batch exceeds size limit") from exc
            raise
        finally:
            for path in paths:
                path.unlink(missing_ok=True)

    @router.get("/{todo_id}/attachments/{attachment_id}")
    def download(todo_id: int, attachment_id: int, inline: bool = False,
                 principal: Principal = Depends(authenticate_token)):
        with todos.SessionLocal() as db:
            user = todos._user(db, principal)
            todos._todo(db, todo_id, user)
            item = db.get(TodoAttachment, attachment_id)
            if item is None or item.task_id != todo_id:
                raise HTTPException(404, "Attachment not found")
            path = attachment_path(item.stored_filename)
            if not path.is_file():
                raise HTTPException(404, "Attachment file not found")
            preview = inline and (item.content_type.startswith("image/") or item.content_type == "application/pdf")
            return FileResponse(path, media_type=item.content_type, filename=item.original_filename,
                content_disposition_type="inline" if preview else "attachment",
                headers={"X-Content-Type-Options": "nosniff", "Cache-Control": "private, no-store",
                         "Content-Security-Policy": "sandbox; default-src 'none'", "Referrer-Policy": "no-referrer"})

    @router.delete("/{todo_id}/attachments/{attachment_id}", status_code=204)
    def delete(todo_id: int, attachment_id: int, principal: Principal = Depends(authenticate_token)):
        with todos.SessionLocal() as db:
            user = todos._user(db, principal)
            todo = todos._todo(db, todo_id, user)
            item = db.get(TodoAttachment, attachment_id)
            if item is None or item.task_id != todo_id:
                raise HTTPException(404, "Attachment not found")
            if not serialize(db, item, user, todo)["can_delete"]:
                raise HTTPException(403, "You cannot remove this attachment")
            path = attachment_path(item.stored_filename)
            db.delete(item)
            db.commit()
            path.unlink(missing_ok=True)
