from fastapi import APIRouter, Depends, Header, Body, HTTPException
from typing import Any

from sqlalchemy.orm import Session 
from app.config import Settings
from app.services.webhook_service import save_event
from app.db.database import get_db
from app.services.normalizers.factory import normalize_event

router = APIRouter()

# 1. import Settings and HTTPException
settings = Settings()

# 2. get the secret from config
secret_token = settings.gitlab_token
# 3. compare incoming token to secret
allowed_events = ["Push Hook", "Pipeline Hook", "Deployment Hook", "Merge Request Hook"]  # Example allowed events
@router.post("/gitlab")
async def gitlab_webhook(x_gitlab_token:str = Header(...), x_gitlab_event:str = Header(...), payload:Any = Body(...), db: Session = Depends(get_db)):
    if (x_gitlab_token != secret_token):
        raise HTTPException(status_code=401, detail="Unauthorized")
    if (x_gitlab_event not in allowed_events):
        return {"message": f"Event '{x_gitlab_event}' is not allowed. Ignoring."}

    # 4. process the payload
    normalized= normalize_event(provider='gitlab', payload=payload)
    event = save_event(normalized, db,provider='gitlab')
    db.commit()  # Commit the transaction to save the event in the database
    print("Received GitLab webhook with payload:", payload)
    return {"message": "Webhook received successfully"}

@router.post("/github")
async def github_webhook(x_hub_signature_256:str=Header(None),x_github_event:str =Header(...),payload:Any =Body(...),db:Session=Depends(get_db)):
    allowed_github_events=["push","workflow_run","pull_request"]
    if x_github_event not in allowed_github_events:
        return{"message":f"Event '{x_github_event}' is not allowed.Ignoring"}
    normalized = normalize_event(provider='github', payload=payload, event=x_github_event)
    event = save_event(normalized,db,provider='github')
    db.commit()
    return {"message":"Github webhook received successfully"}