from starlette.responses import JSONResponse


class _PayloadLimitExceeded(Exception):
    pass


class NotificationBodyLimitMiddleware:
    """Bound notification ingestion bodies, including chunked requests."""

    def __init__(self, app, max_bytes: int = 65536):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope, receive, send):
        if scope.get("type") != "http" or scope.get("method") != "POST" or scope.get("path") != "/api/v1/notifications":
            await self.app(scope, receive, send)
            return

        content_length = next((value for key, value in scope.get("headers", []) if key.lower() == b"content-length"), None)
        if content_length is not None:
            try:
                if int(content_length) > self.max_bytes:
                    response = JSONResponse({"detail": "Notification payload is too large"}, status_code=413)
                    await response(scope, receive, send)
                    return
            except ValueError:
                response = JSONResponse({"detail": "Invalid request size"}, status_code=400)
                await response(scope, receive, send)
                return

        received = 0

        async def bounded_receive():
            nonlocal received
            message = await receive()
            if message.get("type") == "http.request":
                received += len(message.get("body", b""))
                if received > self.max_bytes:
                    raise _PayloadLimitExceeded
            return message

        try:
            await self.app(scope, bounded_receive, send)
        except _PayloadLimitExceeded:
            response = JSONResponse({"detail": "Notification payload is too large"}, status_code=413)
            await response(scope, receive, send)
