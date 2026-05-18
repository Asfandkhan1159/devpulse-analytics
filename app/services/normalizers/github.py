
def normalize_github_event(payload:dict,event:str)-> dict:
    repository = payload.get("repository",{})
    if event == "workflow_run":
        workflow = payload.get("workflow_run",{})
        return{
            "external_id":str(repository.get("id")),
            "project_name":repository.get("name"),
            "web_url":repository.get("html_url"),
            "event_type":"pipeline",
            "status":workflow.get("conclusion"),
            "created_at":workflow.get("created_at"),
            "finished_at":workflow.get("finished_at")
        }
    elif event == "pull_request":
        pr = payload.get("pull_request",{})
        return{
            "external_id":str(repository.get("id")),
            "project_name":str(repository.get("name")),
            "web_url":repository.get("html_url"),
            "event_type":"merge_request",
            "status": "success" if pr.get("merged") else pr.get("state"),
            "created_at":pr.get("created_at"),
            "finished_at":pr.get("merged_at"),
        }
    raise ValueError(f"Unsupported Github event:{event}")