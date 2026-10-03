import io
import os
import uuid

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from renderer import render_code128, render_pdf417

OUTPUT_DIR = os.environ.get("OUTPUT_DIR", "./uploads/barcodes")
RENDER_PUBLIC_URL = os.environ.get(
    "RENDER_PUBLIC_URL", "http://localhost:8000/files"
)

STORAGE_ENDPOINT = os.environ.get("STORAGE_ENDPOINT", "").strip()
STORAGE_BUCKET = os.environ.get("STORAGE_BUCKET", "barcodes")
STORAGE_ACCESS_KEY = os.environ.get("STORAGE_ACCESS_KEY", "")
STORAGE_SECRET_KEY = os.environ.get("STORAGE_SECRET_KEY", "")
STORAGE_USE_SSL = os.environ.get("STORAGE_USE_SSL", "false").lower() == "true"
STORAGE_PUBLIC_URL = os.environ.get("STORAGE_PUBLIC_URL", "").rstrip("/")

os.makedirs(OUTPUT_DIR, exist_ok=True)

app = FastAPI(title="barcode-render", version="1.0.0")

# В локальном режиме (без MinIO) сервис сам отдаёт PNG по /files.
# В prod объект отдаёт MinIO через envoy (/storage/), локальный диск не нужен.
if not STORAGE_ENDPOINT:
    app.mount("/files", StaticFiles(directory=OUTPUT_DIR), name="files")


class RenderRequest(BaseModel):
    format: str
    payload: str
    config: str | None = None
    renderKey: str | None = None


def _put_object(object_key: str, content: bytes) -> None:
    from minio import Minio

    client = Minio(
        STORAGE_ENDPOINT,
        access_key=STORAGE_ACCESS_KEY,
        secret_key=STORAGE_SECRET_KEY,
        secure=STORAGE_USE_SSL,
    )
    if not client.bucket_exists(STORAGE_BUCKET):
        client.make_bucket(STORAGE_BUCKET)
    client.put_object(
        STORAGE_BUCKET,
        object_key,
        io.BytesIO(content),
        length=len(content),
        content_type="image/png",
    )


def _store(object_key: str, content: bytes) -> str:
    if STORAGE_ENDPOINT:
        _put_object(object_key, content)
        base = STORAGE_PUBLIC_URL or f"http://{STORAGE_ENDPOINT}"
        return f"{base}/{STORAGE_BUCKET}/{object_key}"

    with open(os.path.join(OUTPUT_DIR, object_key), "wb") as fh:
        fh.write(content)
    return f"{RENDER_PUBLIC_URL}/{object_key}"


@app.get("/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/render")
def render(req: RenderRequest) -> dict[str, str]:
    render_key = req.renderKey or uuid.uuid4().hex
    fmt = req.format.lower()

    try:
        if fmt == "pdf417":
            content = render_pdf417(req.payload, req.config or "")
        elif fmt == "code128":
            content = render_code128(req.payload)
        else:
            raise ValueError(f"Unsupported format: {req.format}")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    object_key = f"{render_key}.png"
    url = _store(object_key, content)
    return {"key": object_key, "url": url}


@app.get("/")
def root() -> dict[str, str]:
    return {"service": "barcode-render"}
