from fastapi import FastAPI
from app.api.v1.api import api_router

app = FastAPI(
    title="SaaS MVP API",
    description="Backend API for the SaaS MVP starter",
    version="1.0.0",
)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def health_check():
    return {"status": "ok", "message": "SaaS MVP API is running"}