"""Run explicitly: PLAYWRIGHT_BROWSERS_PATH=... python tests/browser_todos.py.
Uses an isolated database and routes Chromium requests through FastAPI TestClient.
Requires the optional playwright package and Chromium runtime.
"""
import os
import base64
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from playwright.sync_api import sync_playwright, expect
from test_todo_attachments import AttachmentTests
from app.auth import SESSION_COOKIE_NAME

fixture = AttachmentTests()
fixture.setUp()
try:
    fixture.client.cookies.set(SESSION_COOKIE_NAME, fixture.tokens["alice"]["Authorization"].split(" ", 1)[1])
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel=os.environ.get("WATCHTOWER_BROWSER_CHANNEL") or None)
        page = browser.new_page(viewport={"width": 1440, "height": 1000})
        page.add_init_script("""
          window.uploadProgressEvents = [];
          const send = XMLHttpRequest.prototype.send;
          XMLHttpRequest.prototype.send = function(...args) {
            this.upload.addEventListener('progress', event => window.uploadProgressEvents.push(event.loaded));
            const result = send.apply(this, args);
            // Route fulfillment bypasses network progress; exercise the UI handler
            // with a deterministic native ProgressEvent.
            this.upload.dispatchEvent(new ProgressEvent('progress', {lengthComputable:true, loaded:50, total:100}));
            window.lastRenderedProgress = document.querySelector('#todo-upload-progress')?.value;
            return result;
          };
        """)
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        def route_request(route):
            request = route.request
            if not request.url.startswith("http://testserver/"):
                route.abort()
                return
            headers = {key: value for key, value in request.headers.items() if key not in {"cookie", "host", "content-length"}}
            response = fixture.client.request(request.method, request.url,
                headers=headers, content=request.post_data_buffer)
            route.fulfill(status=response.status_code, headers=dict(response.headers), body=response.content)
        page.route("**/*", route_request)
        page.goto("http://testserver/todos")
        expect(page.locator("[data-open-task]").first).to_be_visible()
        page.locator("[data-open-task]").first.click()
        expect(page.locator("#todo-dialog")).to_be_visible()
        expect(page.locator("#todo-title")).to_have_value("Prepare release")
        page.locator("#todo-title").fill("Release checklist")
        page.locator("#todo-save").click()
        expect(page.locator("#todo-dialog")).not_to_be_visible()
        page.locator("[data-open-task]").first.click()
        expect(page.locator("#todo-title")).to_have_value("Release checklist")
        page.locator("#todo-files").set_input_files([
            {"name": "notes.txt", "mimeType": "text/plain", "buffer": b"Release notes"},
            {"name": "report.pdf", "mimeType": "application/pdf", "buffer": b"%PDF-1.4\n%%EOF"},
        ])
        expect(page.locator(".todo-attachment")).to_have_count(2)
        # Actual DOM drop and clipboard events use the same native File API as users.
        png = base64.b64encode(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII=")).decode()
        page.evaluate("""b64 => {
          const data = new DataTransfer();
          data.items.add(new File([Uint8Array.from(atob(b64), c => c.charCodeAt(0))], 'drop.png', {type:'image/png'}));
          document.querySelector('#todo-dialog').dispatchEvent(new DragEvent('drop', {dataTransfer:data, bubbles:true, cancelable:true}));
        }""", png)
        expect(page.locator(".todo-attachment")).to_have_count(3)
        page.evaluate("""b64 => {
          const data = new DataTransfer();
          data.items.add(new File([Uint8Array.from(atob(b64), c => c.charCodeAt(0))], 'paste.png', {type:'image/png'}));
          document.querySelector('#todo-title').dispatchEvent(new ClipboardEvent('paste', {clipboardData:data, bubbles:true, cancelable:true}));
        }""", png)
        expect(page.locator(".todo-attachment")).to_have_count(4)
        expect(page.locator("#todo-upload-progress")).to_be_hidden()
        assert page.evaluate("window.uploadProgressEvents.some(bytes => bytes > 0) && window.lastRenderedProgress === 50")
        expect(page.locator(".todo-attachment img")).to_have_count(2)
        page.wait_for_function("Array.from(document.querySelectorAll('.todo-attachment img')).every(img => img.complete && img.naturalWidth > 0)")
        page.screenshot(path="/tmp/watchtower-todos-light.png")
        page.keyboard.press("Escape")
        expect(page.locator("#todo-dialog")).not_to_be_visible()
        page.locator("#theme-toggle").click()
        expect(page.locator("html")).to_have_attribute("data-theme", "dark")
        page.locator("[data-open-task]").first.click()
        page.screenshot(path="/tmp/watchtower-todos-dark.png")
        page.set_viewport_size({"width": 390, "height": 844})
        page.screenshot(path="/tmp/watchtower-todos-mobile.png")
        assert page.locator("#todo-dialog").bounding_box()["width"] <= 390
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        page.on("dialog", lambda dialog: dialog.accept())
        page.locator("[data-remove-attachment]").first.click()
        expect(page.locator(".todo-attachment")).to_have_count(3)
        page.keyboard.press("Escape")
        page.goto(f"http://testserver/todos?task={fixture.task['id']}")
        expect(page.locator("#todo-dialog")).to_be_visible()
        assert not errors, errors
        browser.close()
        print("PASS: editing, panel, Escape, multi-upload, drop, paste, images, deletion, deep link, themes and mobile layout")
finally:
    fixture.tearDown()
    fixture.doCleanups()
