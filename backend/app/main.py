"""
main.py — FastAPI app for ENSECNET CiscoParser.

Parse a Cisco IOS-XE running-config into a NetBox-ready digital model,
and optionally push it straight into NetBox (DCIM/IPAM + config context).

Endpoints:
  GET  /api/health           - liveness
  POST /api/test-connection  - verify NetBox URL + token
  POST /api/parse            - upload .cfg file, return model
  POST /api/parse-text       - parse from raw text body
  POST /api/push             - push model to NetBox
"""
import os
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from app.parser import CiscoParser
from app.transform import transform
from app.netbox_push import NetBoxPusher

app = FastAPI(title="ENSECNET CiscoParser", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

NETBOX_URL = os.getenv("NETBOX_URL", "")
NETBOX_TOKEN = os.getenv("NETBOX_TOKEN", "")


class TextBody(BaseModel):
    config: str


class ConnBody(BaseModel):
    url: str | None = None
    token: str | None = None


class PushBody(BaseModel):
    model: dict
    url: str | None = None
    token: str | None = None


def _creds(url, token):
    return url or NETBOX_URL, token or NETBOX_TOKEN


@app.get("/api/health")
def health():
    return {"status": "ok", "netbox_configured": bool(NETBOX_URL)}


@app.post("/api/test-connection")
def test_connection(body: ConnBody):
    url, token = _creds(body.url, body.token)
    if not url or not token:
        raise HTTPException(400, "NetBox URL and token required")
    try:
        pusher = NetBoxPusher(url, token)
        ver = pusher.nb.status()
        return {"ok": True, "netbox_version": ver.get("netbox-version", "unknown")}
    except Exception as e:
        raise HTTPException(502, f"NetBox connection failed: {e}")


@app.post("/api/parse")
async def parse_file(file: UploadFile = File(...)):
    raw = (await file.read()).decode("utf-8", errors="replace")
    parsed = CiscoParser(raw).parse_all()
    return transform(parsed)


@app.post("/api/parse-text")
def parse_text(body: TextBody):
    parsed = CiscoParser(body.config).parse_all()
    return transform(parsed)


@app.post("/api/push")
def push(body: PushBody):
    url, token = _creds(body.url, body.token)
    if not url or not token:
        raise HTTPException(400, "NetBox URL and token required")
    try:
        result = NetBoxPusher(url, token).push(body.model)
        return {"ok": True, **result}
    except Exception as e:
        raise HTTPException(502, f"Push failed: {e}")
