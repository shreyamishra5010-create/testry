import os
from contextlib import asynccontextmanager
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).parent / ".env")

from fastapi import APIRouter, FastAPI, Request  # noqa: E402
from fastapi.exceptions import RequestValidationError  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402
from starlette.exceptions import HTTPException as StarletteHTTPException  # noqa: E402
from starlette.middleware.cors import CORSMiddleware  # noqa: E402

from taskboard.db import client, ensure_indexes  # noqa: E402
from taskboard.routes import auth, boards, columns, tasks  # noqa: E402
from taskboard.seed import seed_demo  # noqa: E402


@asynccontextmanager
async def lifespan(app: FastAPI):
    await ensure_indexes()
    await seed_demo()
    yield
    client.close()


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)

api = APIRouter(prefix="/api")
for module in (auth, boards, columns, tasks):
    api.include_router(module.router)


@api.get("/health")
async def api_health():
    return {"ok": True, "service": "task-board-api"}


app.include_router(api)


@app.get("/health")
async def health():
    return {"ok": True}


@app.exception_handler(StarletteHTTPException)
async def http_error(request: Request, exc: StarletteHTTPException):
    message = exc.detail if isinstance(exc.detail, str) else "Request failed."
    if message == "Not Found":
        message = "Not found."
    return JSONResponse({"error": message}, status_code=exc.status_code)


@app.exception_handler(RequestValidationError)
async def validation_error(request: Request, exc: RequestValidationError):
    return JSONResponse({"error": "Invalid request body."}, status_code=400)


@app.middleware("http")
async def security_headers(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response


app.add_middleware(
    CORSMiddleware,
    allow_origins=[o.strip() for o in os.environ.get("CORS_ORIGINS", "*").split(",")],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)
