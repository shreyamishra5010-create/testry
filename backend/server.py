# Launcher: the platform starts this ASGI app; it boots the Node/Express API and forwards requests to it.
import asyncio
import os
import subprocess
from contextlib import asynccontextmanager
from pathlib import Path

import httpx
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from fastapi.responses import Response

ROOT = Path(__file__).parent
load_dotenv(ROOT / ".env")
NODE_URL = f"http://127.0.0.1:{os.environ['API_PORT']}"
HOP = {"host", "content-length", "transfer-encoding", "connection", "content-encoding", "keep-alive"}


@asynccontextmanager
async def lifespan(app: FastAPI):
    proc = subprocess.Popen(["node", "server.js"], cwd=ROOT, env=os.environ.copy())
    app.state.client = httpx.AsyncClient(base_url=NODE_URL, timeout=30)
    for _ in range(100):
        try:
            await app.state.client.get("/api/health")
            break
        except httpx.TransportError:
            await asyncio.sleep(0.1)
    yield
    await app.state.client.aclose()
    proc.terminate()
    proc.wait(timeout=5)


app = FastAPI(lifespan=lifespan, docs_url=None, redoc_url=None, openapi_url=None)


@app.api_route("/{path:path}", methods=["GET", "POST", "PATCH", "PUT", "DELETE", "OPTIONS"])
async def proxy(path: str, request: Request):
    upstream = await request.app.state.client.request(
        request.method,
        f"/{path}",
        params=request.query_params,
        content=await request.body(),
        headers={k: v for k, v in request.headers.items() if k.lower() not in HOP},
    )
    headers = {k: v for k, v in upstream.headers.items() if k.lower() not in HOP}
    return Response(upstream.content, upstream.status_code, headers)
