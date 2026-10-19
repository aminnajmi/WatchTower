import unittest
import io
import zipfile
from pathlib import Path
from unittest.mock import patch

from sqlalchemy import select
from app.config import settings
from app.models import TodoAttachment
import test_todos


class AttachmentTests(unittest.TestCase):
    create = test_todos.TodoTests.create
    tearDown = test_todos.TodoTests.tearDown
    def setUp(self):
        test_todos.TodoTests.setUp(self)
        self.storage = Path(self.temp_dir.name) / "attachments"
        self.storage_patch = patch.object(settings, "todo_attachment_dir", str(self.storage))
        self.storage_patch.start()
        self.addCleanup(self.storage_patch.stop)
        self.task = self.create(assigned_to_user_id=self.ids["bob"]).json()
        self.url = f"/api/v1/todos/{self.task['id']}/attachments"

    def upload(self, files=None, who="alice"):
        return self.client.post(self.url, headers=self.tokens[who], files=files or [("files", ("notes.txt", b"Task notes", "text/plain"))])

    def test_batch_download_preview_and_persistence(self):
        response = self.upload([
            ("files", ("screen.png", b"\x89PNG\r\n\x1a\nimage", "image/png")),
            ("files", ("report.pdf", b"%PDF-1.4\n%%EOF", "application/pdf")),
        ])
        self.assertEqual(response.status_code, 201, response.text)
        files = response.json()
        self.assertEqual(len(files), 2)
        # Dispose connections, then reopen: metadata and bytes are persistent.
        self.engine.dispose()
        listed = self.client.get(self.url, headers=self.tokens["bob"]).json()
        self.assertEqual(len(listed), 2)
        self.assertEqual(len(list(self.storage.iterdir())), 2)
        for item in listed:
            url = f"{self.url}/{item['id']}"
            preview = self.client.get(url + "?inline=true", headers=self.tokens["bob"])
            self.assertEqual(preview.status_code, 200)
            self.assertTrue(preview.headers["content-disposition"].startswith("inline;"))
            self.assertEqual(preview.headers["x-content-type-options"], "nosniff")
            self.assertIn("sandbox", preview.headers["content-security-policy"])
            download = self.client.get(url, headers=self.tokens["alice"])
            self.assertTrue(download.headers["content-disposition"].startswith("attachment;"))
        todo = self.client.get(f"/api/v1/todos/{self.task['id']}", headers=self.tokens["alice"]).json()
        self.assertEqual(todo["attachment_count"], 2)

    def test_permissions_cross_task_and_reassignment(self):
        item = self.upload(who="bob").json()[0]
        url = f"{self.url}/{item['id']}"
        for endpoint in [self.url, url]:
            self.assertEqual(self.client.get(endpoint).status_code, 401)
            self.assertEqual(self.client.get(endpoint, headers=self.tokens["carol"]).status_code, 404)
        self.assertEqual(self.upload(who="carol").status_code, 404)
        other = self.create().json()
        self.assertEqual(self.client.get(f"/api/v1/todos/{other['id']}/attachments/{item['id']}", headers=self.tokens["alice"]).status_code, 404)
        self.client.patch(f"/api/v1/todos/{self.task['id']}", headers=self.tokens["alice"], json={"assigned_to_user_id": self.ids["carol"]})
        self.assertEqual(self.client.get(url, headers=self.tokens["bob"]).status_code, 404)
        self.assertEqual(self.client.delete(url, headers=self.tokens["carol"]).status_code, 403)
        self.assertEqual(self.client.delete(url, headers=self.tokens["alice"]).status_code, 204)
        self.assertEqual(list(self.storage.iterdir()), [])

    def test_limits_types_and_batch_rollback(self):
        with patch.object(settings, "todo_attachment_max_bytes", 4):
            self.assertEqual(self.upload().status_code, 413)
            self.assertEqual(self.upload([("files", ("huge.txt", b"x" * 70000))]).status_code, 413)
        self.assertEqual(self.upload([("files", ("x.html", b"<script>x</script>", "text/html"))]).status_code, 415)
        self.assertEqual(self.upload([("files", ("x.png", b"<script>x</script>", "image/png"))]).status_code, 415)
        response = self.upload([("files", ("ok.txt", b"okay")), ("files", ("bad.exe", b"bad"))])
        self.assertEqual(response.status_code, 415)
        self.assertEqual(list(self.storage.iterdir()), [])
        self.assertEqual(self.upload([("files", ("empty.txt", b""))]).status_code, 422)
        with patch.object(settings, "todo_attachment_max_count", 1):
            self.assertEqual(self.upload().status_code, 201)
            self.assertEqual(self.upload().status_code, 422)

    def test_filename_safety_and_task_cleanup(self):
        item = self.upload([("files", ("../../evil.txt", b"safe", "text/html"))]).json()[0]
        self.assertEqual(item["original_filename"], "evil.txt")
        with self.sessions() as db:
            record = db.get(TodoAttachment, item["id"])
            self.assertRegex(record.stored_filename, r"^[a-f0-9]{32}$")
        response = self.client.get(f"{self.url}/{item['id']}?inline=true", headers=self.tokens["alice"])
        self.assertEqual(response.headers["content-type"], "text/plain; charset=utf-8")
        self.assertTrue(response.headers["content-disposition"].startswith("attachment"))
        self.assertEqual(self.client.delete(f"/api/v1/todos/{self.task['id']}", headers=self.tokens["alice"]).status_code, 204)
        self.assertEqual(list(self.storage.iterdir()), [])
        with self.sessions() as db:
            self.assertIsNone(db.scalar(select(TodoAttachment)))

    def test_internal_path_traversal_rejected(self):
        item = self.upload().json()[0]
        with self.sessions.begin() as db:
            db.get(TodoAttachment, item["id"]).stored_filename = "../secret"
        self.assertEqual(self.client.get(f"{self.url}/{item['id']}", headers=self.tokens["alice"]).status_code, 404)

    def test_office_archive_and_text_formats(self):
        for extension, marker in [("docx", "word/document.xml"), ("xlsx", "xl/workbook.xml"), ("zip", "notes.txt")]:
            content = io.BytesIO()
            with zipfile.ZipFile(content, "w") as archive:
                archive.writestr("[Content_Types].xml", "<Types/>")
                archive.writestr(marker, "example")
            self.assertEqual(self.upload([("files", (f"example.{extension}", content.getvalue()))]).status_code, 201)
        self.assertEqual(self.upload([("files", ("bad.docx", b"PKwrong"))]).status_code, 415)
