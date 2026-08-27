from fastapi import FastAPI
from starlette.responses import JSONResponse

from src.models.base.exception import ServiceException, NoDataForUpdate, NotFoundData


def register_exception_handlers(app: FastAPI):

    @app.exception_handler(ServiceException)
    async def service_handler(request, exc):
        return JSONResponse(status_code=500, content={"detail": "Server Error"})

    @app.exception_handler(NoDataForUpdate)
    async def service_handler(request, exc):
        return JSONResponse(status_code=400, content={"detail": "Did not transmit data"})

    @app.exception_handler(NotFoundData)
    async def service_handler(request, exc):
        return JSONResponse(status_code=404, content={"detail": "Not found data"})
