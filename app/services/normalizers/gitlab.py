def normalize_gitlab_event(payload: dict):
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
            "status": object_attributes.get("status"),
            "created_at": object_attributes.get("created_at"),
            "finished_at": object_attributes.get("finished_at"),
            "actor": user.get("name"),
            "branch": object_attributes.get("ref"),
            "commit_count": None,
            "external_event_id": str(payload.get("id")),
        }
    else:
        # Backfill API payload — pipeline or MR
        is_mr = payload.get("merged_at") is not None or payload.get("merge_status") is not None
        if is_mr:
            return {
                "external_id": str(payload.get("project_id")),
                "project_name": None,
                "web_url": payload.get("web_url"),
                "event_type": "merge_request",
                "status": "success" if payload.get("merged_at") else payload.get("state"),
                "created_at": payload.get("created_at"),
                "finished_at": payload.get("merged_at"),
                "actor": payload.get("author", {}).get("name"),
                "branch": payload.get("source_branch"),
                "commit_count": None,
                "external_event_id": str(payload.get("id")),
            }
        else:
            # Pipeline
            return {
                "external_id": str(payload.get("project_id")),
                "project_name": None,
                "web_url": payload.get("web_url"),
                "event_type": "pipeline",
                "status": payload.get("status"),
                "created_at": payload.get("created_at"),
                "finished_at": payload.get("updated_at"),
                "actor": None,
                "branch": payload.get("ref"),
                "commit_count": None,
                "external_event_id": str(payload.get("id")),
            }