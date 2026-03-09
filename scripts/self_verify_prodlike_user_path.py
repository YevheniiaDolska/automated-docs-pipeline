#!/usr/bin/env python3
"""Extended self-verification for prod-like sandbox endpoints."""

from __future__ import annotations

import argparse
import json
import urllib.error
import urllib.request


def call_json(method: str, url: str, body: dict | None = None) -> tuple[int, dict | None]:
    data = None
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": "Bearer demo-token",
        "X-Request-Id": "req_prodlike_user_path",
    }
    if body is not None:
        data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(url=url, method=method, headers=headers, data=data)
    try:
        with urllib.request.urlopen(req, timeout=20) as response:
            status = response.getcode()
            payload = response.read().decode("utf-8")
            return status, (json.loads(payload) if payload else None)
    except urllib.error.HTTPError as error:
        payload = error.read().decode("utf-8")
        return error.code, (json.loads(payload) if payload else None)


def require(cond: bool, msg: str) -> None:
    if not cond:
        raise RuntimeError(msg)


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify prod-like user path")
    parser.add_argument("--base-url", default="http://localhost:4011/v1")
    args = parser.parse_args()
    b = args.base_url.rstrip("/")

    status, me = call_json("GET", f"{b}/users/me")
    require(status == 200 and isinstance(me, dict) and me.get("id"), f"GET /users/me failed: {status}")
    user_id = me["id"]

    status, project = call_json(
        "POST",
        f"{b}/projects",
        {
            "name": "Prod-like validation project",
            "description": "Created by automated user path",
            "owner_id": user_id,
        },
    )
    require(status == 201 and isinstance(project, dict), f"POST /projects failed: {status}")
    project_id = project["id"]

    status, task = call_json(
        "POST",
        f"{b}/tasks",
        {
            "project_id": project_id,
            "title": "Validate prod-like task flow",
            "description": "Task created by self-check",
            "assignee_id": user_id,
            "priority": "high",
        },
    )
    require(status == 201 and isinstance(task, dict), f"POST /tasks failed: {status}")
    task_id = task["id"]

    status, tag = call_json("POST", f"{b}/tags", {"name": "api-first", "slug": "api-first", "color": "#2563eb"})
    if status not in (201, 409):
        require(False, f"POST /tags unexpected status: {status}")
    if status == 201:
        tag_id = tag["id"]
    else:
        status, tags = call_json("GET", f"{b}/tags?q=api-first")
        require(status == 200 and tags and tags.get("data"), "GET /tags fallback failed")
        tag_id = tags["data"][0]["id"]

    status, _ = call_json("POST", f"{b}/tasks/{task_id}/tags/{tag_id}")
    require(status == 204, f"POST /tasks/{{id}}/tags/{{id}} failed: {status}")

    status, comment = call_json("POST", f"{b}/tasks/{task_id}/comments", {"author_id": user_id, "body": "Looks good"})
    require(status == 201 and comment and comment.get("id"), f"POST /tasks/{{id}}/comments failed: {status}")
    comment_id = comment["id"]

    status, _ = call_json("POST", f"{b}/tasks/{task_id}/complete")
    require(status == 204, f"POST /tasks/{{id}}/complete failed: {status}")

    status, task_read = call_json("GET", f"{b}/tasks/{task_id}")
    require(status == 200 and task_read and task_read.get("status") == "done", "GET /tasks/{id} not done")

    status, user_tasks = call_json("GET", f"{b}/users/{user_id}/tasks?limit=5")
    require(status == 200 and isinstance(user_tasks, dict) and "data" in user_tasks, "GET /users/{id}/tasks failed")

    status, _ = call_json("DELETE", f"{b}/comments/{comment_id}")
    require(status == 204, f"DELETE /comments/{{id}} failed: {status}")

    print("Prod-like API user-path self-verification passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
