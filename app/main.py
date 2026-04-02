from fastapi import FastAPI

from app.config import Settings

from app.routers import webhooks
app = FastAPI()
settings = Settings()

print(f"GitLab Token from config: {settings.gitlab_token}")

app.include_router(webhooks.router, prefix="/webhooks", tags=["webhooks"])
@app.get("/")
def read_root():
    return {"i am up": "& running successfully.!! ASFAND says hi tosdsad."}

