from fastapi import FastAPI

from app.config import Settings
from app.routers import metrics
from app.routers import webhooks
app = FastAPI()
settings = Settings()

print(f"GitLab Token from config: {settings.gitlab_token}")

#Decoraters to include the routers for webhooks and metrics
app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
app.include_router(metrics.router, prefix="/metrics", tags=["metrics"])

#Root endpoint for basic health check

@app.get("/")
def read_root():
    return {"i am up": "& running successfully.!! ASFAND says hi tosdsad."}

@app.get("/stats")
def health_check():
    return {"stats": "statx are healthy and up to date."}    