from __future__ import annotations

import os

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from web.timeline_utils import group_events, parse_timestamp

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

    timeline_events = sorted(events, key=lambda event: parse_timestamp(event.get("timestamp")), reverse=True)
    grouped_events = group_events(timeline_events)
    event_types = sorted(
        {
            str(event.get("event_type", "-"))
            for event in timeline_events
            if str(event.get("event_type", "")).strip()
        }
    )

    return templates.TemplateResponse(
        request=request,
        name="timeline.html",
        context={
            "events": grouped_events,
            "event_types": event_types,
            "error_message": error_message,
        },
    )


@app.get("/api/devices")
async def proxy_devices() -> JSONResponse:
    devices_url = f"{BACKEND_API_URL}/api/devices"

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(devices_url)
            response.raise_for_status()
            return JSONResponse(status_code=response.status_code, content=response.json())
    except Exception as error:
        return JSONResponse(
            status_code=502,
            content={"items": [], "error": f"Unable to load devices from API: {error}"},
        )
