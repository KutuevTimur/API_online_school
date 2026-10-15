"""Bound multipart spooling before FastAPI has parsed UploadFile objects."""
from starlette.formparsers import MultiPartException
from starlette.responses import JSONResponse


class MultipartBodyLimitMiddleware:
    # 100 MiB source budget plus bounded multipart overhead; each file is then
    # independently limited to 20 MiB by the authenticated domain upload handler.
    def __init__(self, app, max_bytes: int = 102 * 1024 * 1024) -> None:
        self.app, self.max_bytes = app, max_bytes

    async def __call__(self, scope, receive, send) -> None:
        headers = dict(scope.get('headers', []))
        if scope['type'] != 'http' or not headers.get(b'content-type', b'').lower().startswith(b'multipart/form-data'):
            await self.app(scope,receive,send)
            return
        try:
            length = int(headers.get(b'content-length', b'0'))
        except ValueError:
            length = 0
        if length > self.max_bytes:
            await JSONResponse({'detail':'Multipart request exceeds 102 MiB'},status_code=413)(scope,receive,send)
            return
        received = 0
        exceeded = False
        async def limited_receive():
            nonlocal received, exceeded
            message = await receive()
            if message['type'] == 'http.request':
                received += len(message.get('body',b''))
                if received > self.max_bytes:
                    exceeded = True
                    # Starlette closes every spooled part for MultiPartException.
                    raise MultiPartException('Multipart request exceeds 102 MiB')
            return message
        async def limited_send(message):
            if exceeded and message['type'] == 'http.response.start':
                message = {**message, 'status':413}
            await send(message)
        await self.app(scope,limited_receive,limited_send)
