
def normalize_gitlab_event(payload:dict):
    object_attributes = payload.get("object_attributes",{})
    project=payload.get("project",{})

    return{
        "external_id":str(project.get("id")),
        "project_name":str(project.get("name")),
        "web_url":str(project.get("web_url")),
        "event_type":payload.get("object_kind"),
        "status":object_attributes.get("status"),
        "created_at":object_attributes.get("created_at"),
        "finished_at":object_attributes.get("finished_at")
    }