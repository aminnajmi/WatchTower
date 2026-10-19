# To-Dos and private attachments

The task list keeps the existing creator/admin editing permissions and assignee/admin completion permissions. Task titles and attachment counts open the details drawer. Assignment notifications remain in the Notification Center; their Open task link targets `/todos?task=ID`. Assigning the same user does not emit another notification.

All task participants (creator, current assignee, administrators) may read and upload attachments. The uploader, task creator, or administrator may delete attachments, provided they still have access to the task. Reassignment immediately revokes the previous assignee's access unless they are also the creator.

## Storage and deployment

Startup's existing idempotent `Base.metadata.create_all` migration adds `todo_attachments`. It does not change or reset existing task records. Fields: id, task_id (foreign key), original_filename, stored_filename, file_size, content_type, uploaded_by_user_id (foreign key), created_at.

Docker Compose sets `TODO_ATTACHMENT_DIR=/app/data/todo-attachments`, inside the existing `watchtower-data` volume. Rebuild/recreate the application normally, preserving that volume. No new service, dependency, production .env edit, or CI change is required. Back up this directory together with the database. Do not remove the data volume during deployment.

Outside Docker the default directory is `./data/todo-attachments`. Ensure the application account can create/write it. Files use random internal names and are never exposed through the static mount.

Optional environment settings:
- `TODO_ATTACHMENT_MAX_BYTES`: 20971520 (20 MiB per file).
- `TODO_ATTACHMENT_MAX_COUNT`: 20 attachments per task.
- `TODO_ATTACHMENT_EXTENSIONS`: png,jpg,jpeg,webp,pdf,txt,docx,xlsx,zip. This may restrict the built-in validated formats, not enable arbitrary new formats.
- `TODO_ATTACHMENT_DIR`: private writable persistent directory.

Multipart batches are limited to twice the per-file limit plus 64 KiB multipart overhead, including chunked requests. The browser uploads selected files sequentially, with per-file progress; successfully uploaded files remain if a later file fails. An API batch is atomic: invalid files roll back the whole batch.

## API

All routes require existing session or bearer authentication and current task access:
- `POST /api/v1/todos/{id}/attachments`: multipart, one or more repeated `files` fields.
- `GET /api/v1/todos/{id}/attachments`: metadata and delete permissions.
- `GET /api/v1/todos/{id}/attachments/{attachment_id}`: streamed download.
- Same GET with `?inline=true`: image/PDF preview; other types remain downloads.
- `DELETE /api/v1/todos/{id}/attachments/{attachment_id}`: delete metadata and stored file.

The API checks file signatures/containers and UTF-8 text, sanitizes filenames, and serves private no-store responses with nosniff and sandbox headers. Archives are never extracted and uploads are never executed. Content validation is not malware scanning.

Deleting a task removes its attachment metadata in the database transaction and then removes the files. A process or filesystem failure after committing deletion can leave inaccessible orphan files; restore/backup procedures should account for that. Never delete files based on user-supplied paths.

## Verification

`python -m unittest discover -s tests -q` includes task and attachment API regressions.
`node --check static/js/app.js` checks JavaScript syntax.
The optional `python tests/browser_todos.py` uses Playwright Chromium with an isolated temporary database and storage; it covers drawer editing, Escape, multiple files, drop/paste, rendered thumbnails, deletion, deep links, themes, and mobile bounds. Install Playwright/Chromium in your test environment only; the deployed application has no new frontend framework.
