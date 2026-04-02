from fastapi import APIRouter, Header, Body, HTTPException
from typing import Any
from app.config import Settings


router = APIRouter()

# 1. import Settings and HTTPException
settings = Settings()

# 2. get the secret from config
secret_token = settings.gitlab_token
# 3. compare incoming token to secret
allowed_events = ["Push Hook", "Pipeline Hook", "Deployment Hook", "Merge Request Hook"]  # Example allowed events
@router.post("/gitlab")
async def gitlab_webhook(x_gitlab_token:str = Header(...), x_gitlab_event:str = Header(...), payload:Any = Body(...)):
    if (x_gitlab_token != secret_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if (x_gitlab_event not in allowed_events):
        return {"message": f"Event '{x_gitlab_event}' is not allowed. Ignoring."}

    # 4. process the payload
    print("Received GitLab webhook with payload:", payload)
    return {"message": "Webhook received successfully"}
