from fastapi import FastAPI

from app.routes.ransomware import router as ransomware_router

app = FastAPI()

app.include_router(ransomware_router)


@app.get("/health")
def health_check():
    return {"status": "ok"}