from app.services.normalizers.gitlab import normalize_gitlab_event
from app.services.normalizers.github import normalize_github_event

def normalize_event(provider:str, payload:dict, event:str = None):
    if provider == "gitlab":
        return normalize_gitlab_event(payload)
    if provider == "github":
        return normalize_github_event(payload,event)
    raise ValueError(f"Unsupported provider: {provider}")