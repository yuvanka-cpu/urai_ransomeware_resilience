from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from app.routes.ransomware import router as ransomware_router


app = FastAPI()

app.include_router(ransomware_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}


@app.get("/")
def ransomware_dashboard():
    dashboard = (
        Path(__file__).resolve().parent
        / "static"
        / "ransomware_dashboard.html"
    )
    return FileResponse(dashboard)