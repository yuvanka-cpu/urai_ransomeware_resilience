from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from app.routes.ransomware import router as ransomware_router


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["GET", "POST"],
    allow_headers=["Content-Type"],
)

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