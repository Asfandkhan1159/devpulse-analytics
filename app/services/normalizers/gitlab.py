def normalize_status(raw_status: str) -> str:
    return "failure" if raw_status == "failed" else raw_status

def normalize_status_names(names:str) -> str:
 mapping = {
    "Push Hook": "push",
    "Pipeline Hook": "pipeline",
    "Merge Request Hook": "merge_request"
 }

 return mapping.get(names,"unknown")

def normalize_merge_request_status(names:str)-> str:
    mapping ={
        "opened":"pending",
        "closed":"rejected",
        "locked":"locked"

    }
    return mapping.get(names,"unknown")

def normalize_gitlab_event(payload: dict,event:str = None, gitlab_project_id: str = None):
    # Detect if this is a webhook payload or backfill API payload
    if payload.get("object_attributes"):
        # Webhook payload structure
        object_attributes = payload.get("object_attributes", {})
        project = payload.get("project", {})
        user = payload.get("user", {})
        return {
            "external_id": str(project.get("id")),
            "project_name": str(project.get("name")),
            "web_url": str(project.get("web_url")),
            "event_type": payload.get("object_kind"),
            "status": normalize_status(object_attributes.get("status")),
            "created_at": object_attributes.get("created_at"),
            "finished_at": object_attributes.get("finished_at"),
            "timestamp": object_attributes.get("created_at"),
            "actor": user.get("name"),
            "branch": object_attributes.get("ref"),
            "commit_count": None,
            "external_event_id": str(payload.get("id")),
        }
    else:
        # Backfill API payload — pipeline or MR
        is_mr = payload.get("merged_at") is not None or payload.get("merge_status") is not None
        is_push = event == "push" or payload.get("push_data") is not None
        is_commit = payload.get("committed_date") is not None
        if is_mr:
            return {
                "external_id": str(payload.get("project_id")),
                "project_name": None,
                "web_url": payload.get("web_url"),
                "event_type": "merge_request",
                "status": "success" if payload.get("merged_at") else normalize_merge_request_status(payload.get("state")),
                "created_at": payload.get("created_at"),
                "finished_at": payload.get("merged_at"),
                "timestamp": payload.get("created_at"),
                "actor": payload.get("author", {}).get("name"),
                "branch": payload.get("source_branch"),
                "commit_count": None,
                "external_event_id": str(payload.get("id")),
            }
        elif is_push:
            push_data = payload.get("push_data", {})
            author = payload.get("author", {})
            return {
            "external_id": str(payload.get("project_id")),
            "project_name": None,
            "web_url": None,
            "event_type": "push",
            "status": "success",
            "created_at": payload.get("created_at"),
            "finished_at": None,
            "timestamp": payload.get("created_at"),
            "actor": author.get("name"),
            "actor_email": author.get("public_email"),
            "actor_username": author.get("username"),
            "branch": push_data.get("ref"),
            "commit_count": push_data.get("commit_count"),
            "external_event_id": str(payload.get("id")),
        }
        elif is_commit:
            return {
                "external_id": str(payload.get("project_id") or gitlab_project_id),
                "project_name": None,
                "web_url": None,
                "event_type": "commit",
                "status": "success",
                "created_at": payload.get("committed_date"),
                "finished_at": None,
                "timestamp": payload.get("committed_date"),
                "actor": payload.get("author_name"),
                "actor_email": payload.get("author_email"),
                "actor_username": None,
                "branch": None,
                "commit_count": 1,
                "external_event_id": str(payload.get("id")),
            }

        else:
            # Pipeline
            return {
                "external_id": str(payload.get("project_id")),
                "project_name": None,
                "web_url": payload.get("web_url"),
                "event_type": "pipeline",
                "status": normalize_status(payload.get("status")),
                "created_at": payload.get("created_at"),
                "finished_at": payload.get("updated_at"),
                "timestamp": payload.get("created_at"),
                "actor": None,
                "branch": payload.get("ref"),
                "commit_count": None,
                "external_event_id": str(payload.get("id")),
            }