from fastapi import APIRouter, Depends, Header, Body, HTTPException
from typing import Any
from app.config import Settings
from app.services.webhook_service import save_event
from app.db.database import get_db


router = APIRouter()

# 1. import Settings and HTTPException
settings = Settings()

# 2. get the secret from config
secret_token = settings.gitlab_token
# 3. compare incoming token to secret
allowed_events = ["Push Hook", "Pipeline Hook", "Deployment Hook", "Merge Request Hook"]  # Example allowed events
@router.post("/gitlab")
async def gitlab_webhook(x_gitlab_token:str = Header(...), x_gitlab_event:str = Header(...), payload:Any = Body(...), db = Depends(get_db)):
    if (x_gitlab_token != secret_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if (x_gitlab_event not in allowed_events):
        return {"message": f"Event '{x_gitlab_event}' is not allowed. Ignoring."}

    # 4. process the payload
    event = save_event(payload, db)
    db.commit()  # Commit the transaction to save the event in the database
    print("Received GitLab webhook with payload:", payload)
    return {"message": "Webhook received successfully"}
