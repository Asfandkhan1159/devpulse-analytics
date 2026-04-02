from fastapi import APIRouter, Header, Body, HTTPException
from typing import Any
from app.config import Settings


router = APIRouter()

# 1. import Settings and HTTPException
settings = Settings()

# 2. get the secret from config
secret_token = settings.gitlab_token
# 3. compare incoming token to secret
@router.post("/gitlab")
async def gitlab_webhook(x_gitlab_token:str = Header(...), payload:Any = Body(...)):
    if (x_gitlab_token != secret_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    # 4. process the payload
    print("Received GitLab webhook with payload:", payload)
    return {"message": "Webhook received successfully"}
