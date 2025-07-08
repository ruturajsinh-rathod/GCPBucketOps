import asyncio
from contextlib import asynccontextmanager
from typing import Any, AsyncGenerator

from fastapi import FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi_pagination import add_pagination

from config.config import app_settings
from src import constants
from src.api.handlers import start_exception_handlers
from src.api.v1 import router as v1_router
from src.core.scheduler import periodic_cleanup


def init_routers(_app: FastAPI) -> None:
    """
    Initialize all routers.
    """
    _app.include_router(v1_router)


def root_health_path(_app: FastAPI) -> None:
    """
    Health Check Endpoint.
    """

    @_app.get("/", include_in_schema=False)
    def root() -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": constants.SUCCESS})

    @_app.get("/healthcheck", include_in_schema=False)
    def healthcheck() -> JSONResponse:
        return JSONResponse(status_code=status.HTTP_200_OK, content={"message": constants.SUCCESS})


def init_middlewares(_app: FastAPI) -> None:
    """
    Middleware initialization.
    """
    _app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


# ------------------- LIFESPAN HANDLER -------------------
@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncGenerator[None, Any]:
    """
    Starts periodic cleanup task on app startup.
    """
    cleanup_task = asyncio.create_task(periodic_cleanup())
    print("Cleanup scheduler started.")

    yield

    cleanup_task.cancel()
    print("Cleanup scheduler stopped.")


def create_app(debug: bool = False) -> FastAPI:
    """
    Create a Initialize the FastAPI app.
    """
    _app = FastAPI(
        title=app_settings.APP_NAME,
        version=app_settings.APP_VERSION,
        docs_url="/docs",
        redoc_url="/redoc" if debug else None,
        lifespan=lifespan,
    )
    init_routers(_app)
    root_health_path(_app)
    init_middlewares(_app)
    start_exception_handlers(_app)
    add_pagination(_app)
    return _app


debug_app = create_app(debug=True)
