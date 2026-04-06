from __future__ import annotations

import os

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://mikrotrack-app:8000").rstrip("/")

app = FastAPI(title="MikroTrack Web", version="0.1.0")
templates = Jinja2Templates(directory="web/templates")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/", response_class=HTMLResponse)
async def timeline(request: Request) -> HTMLResponse:
    events_url = f"{BACKEND_API_URL}/api/v1/events"
    events: list[dict[str, object]] = []
    error_message = ""

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(events_url, params={"limit": 200})
            response.raise_for_status()
            events = response.json().get("items", [])
    except Exception as error:
        error_message = f"Unable to load events from API: {error}"

    return templates.TemplateResponse(
        request=request,
        name="timeline.html",
        context={
            "events": list(reversed(events)),
            "backend_api_url": BACKEND_API_URL,
            "error_message": error_message,
        },
    )
