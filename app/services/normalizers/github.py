
def normalize_github_event(payload:dict,event:str)-> dict:
    repository = payload.get("repository") or payload.get("base", {}).get("repo", {})
    if event == "workflow_run":
        workflow = payload.get("workflow_run") or payload
        sender = payload.get("sender") or {}
        return{
            "external_id":str(repository.get("id")),
            "project_name":repository.get("name"),
            "web_url":repository.get("html_url"),
            "event_type":"pipeline",
            "status":workflow.get("conclusion"),
            "created_at":workflow.get("created_at"),
            "finished_at":workflow.get("updated_at"),
            "actor":sender.get("login"),
            "branch":workflow.get("head_branch"),
            "commit_count":None
        }
    elif event == "pull_request":
        pr = payload.get("pull_request",{}) or payload
        return{
            "external_id":str(repository.get("id")),
            "project_name":str(repository.get("name")),
            "web_url":repository.get("html_url"),
            "event_type":"merge_request",
            "status": "success" if pr.get("merged") or pr.get("merged_at") else pr.get("state"),
            "created_at":pr.get("created_at"),
            "finished_at":pr.get("merged_at"),
            "actor":pr.get("user",{}).get("login"),
            "branch":pr.get("head",{}).get("ref"),
            "commit_count":None
        }
    elif event == "push":
        commits = payload.get("commits", [])
        ref = payload.get("ref", "")
        print(f"Raw ref value: {ref}")
        print(f"After replace: {ref.replace('refs/heads/', '')}")
        return{
            "external_id":str(repository.get("id")),
            "project_name":repository.get("name"),
            "web_url":repository.get("html_url"),
            "event_type":"push",
            "status":"success",
            "created_at":payload.get("head_commit",{}).get("timestamp"),
            "finished_at":payload.get("head_commit",{}).get("timestamp"),
            "actor":payload.get("pusher",{}).get("name"),
            "branch": ref.replace("refs/heads/",""),
            "commit_count":len(commits)
        }
    raise ValueError(f"Unsupported Github event:{event}")