from __future__ import annotations

import base64
import json
import os
import sqlite3
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse

DB_PATH = os.environ.get("PRODLIKE_DB_PATH", "/data/prodlike.db")
API_PREFIX = "/v1"


def now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def conn() -> sqlite3.Connection:
    c = sqlite3.connect(DB_PATH)
    c.row_factory = sqlite3.Row
    return c


def encode_cursor(offset: int | None) -> str | None:
    if offset is None:
        return None
    raw = json.dumps({"offset": offset}).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def decode_cursor(cursor: str | None) -> int:
    if not cursor:
        return 0
    try:
        data = json.loads(base64.urlsafe_b64decode(cursor.encode("utf-8")).decode("utf-8"))
        return int(data.get("offset", 0))
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid cursor")


def error_response(status: int, code: str, message: str, request_id: str, details: list[dict[str, Any]] | None = None) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details or [],
            },
            "request_id": request_id,
        },
    )


app = FastAPI(title="TaskStream Prod-like Sandbox")


@app.on_event("startup")
def startup() -> None:
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    with conn() as c:
        c.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
              id TEXT PRIMARY KEY,
              email TEXT NOT NULL,
              full_name TEXT NOT NULL,
              role TEXT NOT NULL,
              status TEXT NOT NULL,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS projects (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              description TEXT,
              status TEXT NOT NULL,
              owner_id TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              archived_at TEXT,
              deleted_at TEXT
            );
            CREATE TABLE IF NOT EXISTS tasks (
              id TEXT PRIMARY KEY,
              project_id TEXT NOT NULL,
              title TEXT NOT NULL,
              description TEXT,
              status TEXT NOT NULL,
              priority TEXT NOT NULL,
              assignee_id TEXT,
              due_date TEXT,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL,
              completed_at TEXT,
              deleted_at TEXT
            );
            CREATE TABLE IF NOT EXISTS comments (
              id TEXT PRIMARY KEY,
              task_id TEXT NOT NULL,
              author_id TEXT NOT NULL,
              body TEXT NOT NULL,
              created_at TEXT NOT NULL,
              updated_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS tags (
              id TEXT PRIMARY KEY,
              name TEXT NOT NULL,
              slug TEXT NOT NULL UNIQUE,
              color TEXT,
              created_at TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS task_tags (
              task_id TEXT NOT NULL,
              tag_id TEXT NOT NULL,
              PRIMARY KEY (task_id, tag_id)
            );
            """
        )

        count = c.execute("SELECT COUNT(1) FROM users").fetchone()[0]
        if count == 0:
            user_id = str(uuid.uuid4())
            c.execute(
                "INSERT INTO users(id,email,full_name,role,status,created_at) VALUES(?,?,?,?,?,?)",
                (user_id, "alex@taskstream.example.com", "Alex Rivera", "admin", "active", now_iso()),
            )

            project_id = str(uuid.uuid4())
            c.execute(
                "INSERT INTO projects(id,name,description,status,owner_id,created_at,updated_at,archived_at,deleted_at) VALUES(?,?,?,?,?,?,?,?,?)",
                (
                    project_id,
                    "API-first rollout",
                    "Planning and execution",
                    "active",
                    user_id,
                    now_iso(),
                    now_iso(),
                    None,
                    None,
                ),
            )

            task_id = str(uuid.uuid4())
            c.execute(
                "INSERT INTO tasks(id,project_id,title,description,status,priority,assignee_id,due_date,created_at,updated_at,completed_at,deleted_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
                (
                    task_id,
                    project_id,
                    "Create API-first demo",
                    "Generate OpenAPI from planning notes",
                    "in_progress",
                    "high",
                    user_id,
                    "2026-03-12",
                    now_iso(),
                    now_iso(),
                    None,
                    None,
                ),
            )


@app.middleware("http")
async def request_id_middleware(request: Request, call_next):
    request_id = request.headers.get("X-Request-Id") or f"req_{uuid.uuid4().hex[:12]}"
    request.state.request_id = request_id
    response = await call_next(request)
    response.headers["X-Request-Id"] = request_id
    return response


def require_auth(authorization: str = Header(default="")) -> None:
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid token")


def row_to_dict(row: sqlite3.Row) -> dict[str, Any]:
    return dict(row)


def list_response(rows: list[dict[str, Any]], limit: int, offset: int) -> dict[str, Any]:
    has_more = len(rows) > limit
    items = rows[:limit]
    next_cursor = encode_cursor(offset + limit) if has_more else None
    return {
        "data": items,
        "page": {
            "next_cursor": next_cursor,
            "has_more": has_more,
        },
    }


@app.get(f"{API_PREFIX}/healthz")
def healthz() -> dict[str, str]:
    return {"status": "ok"}


@app.get(f"{API_PREFIX}/projects")
def list_projects(
    request: Request,
    _: None = Depends(require_auth),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = None,
    status: str | None = None,
    owner_id: str | None = None,
    q: str | None = None,
    sort_by: str = "updated_at",
    sort_order: str = "desc",
):
    allowed_sort = {"created_at", "updated_at", "name"}
    if sort_by not in allowed_sort:
        return error_response(400, "invalid_sort", f"Invalid sort_by. Allowed: {sorted(allowed_sort)}", request.state.request_id)
    if sort_order not in {"asc", "desc"}:
        return error_response(400, "invalid_sort", "sort_order must be asc or desc", request.state.request_id)

    offset = decode_cursor(cursor)
    clauses = ["deleted_at IS NULL"]
    params: list[Any] = []
    if status:
        clauses.append("status = ?")
        params.append(status)
    if owner_id:
        clauses.append("owner_id = ?")
        params.append(owner_id)
    if q:
        clauses.append("(name LIKE ? OR description LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])

    where_sql = " AND ".join(clauses)
    sql = f"SELECT * FROM projects WHERE {where_sql} ORDER BY {sort_by} {sort_order.upper()} LIMIT ? OFFSET ?"
    with conn() as c:
        rows = [row_to_dict(r) for r in c.execute(sql, (*params, limit + 1, offset)).fetchall()]
    return list_response(rows, limit, offset)


@app.post(f"{API_PREFIX}/projects", status_code=201)
def create_project(request: Request, payload: dict[str, Any], _: None = Depends(require_auth)):
    pid = str(uuid.uuid4())
    created = now_iso()
    with conn() as c:
        c.execute(
            "INSERT INTO projects(id,name,description,status,owner_id,created_at,updated_at,archived_at,deleted_at) VALUES(?,?,?,?,?,?,?,?,?)",
            (
                pid,
                payload.get("name", "Untitled project"),
                payload.get("description"),
                payload.get("status", "active"),
                payload.get("owner_id", str(uuid.uuid4())),
                created,
                created,
                None,
                None,
            ),
        )
        row = c.execute("SELECT * FROM projects WHERE id = ?", (pid,)).fetchone()
    return row_to_dict(row)


@app.get(f"{API_PREFIX}/projects/{{project_id}}")
def get_project(project_id: str, request: Request, _: None = Depends(require_auth)):
    with conn() as c:
        row = c.execute("SELECT * FROM projects WHERE id = ? AND deleted_at IS NULL", (project_id,)).fetchone()
    if not row:
        return error_response(404, "not_found", "Project not found", request.state.request_id)
    return row_to_dict(row)


@app.patch(f"{API_PREFIX}/projects/{{project_id}}")
def patch_project(project_id: str, payload: dict[str, Any], request: Request, _: None = Depends(require_auth)):
    allowed = {"name", "description", "status", "owner_id"}
    updates = {k: v for k, v in payload.items() if k in allowed}
    if not updates:
        return error_response(400, "invalid_request", "No updatable fields provided", request.state.request_id)
    set_sql = ", ".join([f"{k} = ?" for k in updates.keys()] + ["updated_at = ?"])
    params = list(updates.values()) + [now_iso(), project_id]
    with conn() as c:
        cur = c.execute(f"UPDATE projects SET {set_sql} WHERE id = ? AND deleted_at IS NULL", params)
        if cur.rowcount == 0:
            return error_response(404, "not_found", "Project not found", request.state.request_id)
        row = c.execute("SELECT * FROM projects WHERE id = ?", (project_id,)).fetchone()
    return row_to_dict(row)


@app.delete(f"{API_PREFIX}/projects/{{project_id}}", status_code=204)
def delete_project(project_id: str, request: Request, _: None = Depends(require_auth)):
    with conn() as c:
        cur = c.execute("UPDATE projects SET deleted_at = ?, updated_at = ? WHERE id = ? AND deleted_at IS NULL", (now_iso(), now_iso(), project_id))
    if cur.rowcount == 0:
        return error_response(404, "not_found", "Project not found", request.state.request_id)
    return Response(status_code=204)


@app.post(f"{API_PREFIX}/projects/{{project_id}}/archive", status_code=204)
def archive_project(project_id: str, request: Request, _: None = Depends(require_auth)):
    with conn() as c:
        cur = c.execute(
            "UPDATE projects SET status = 'archived', archived_at = ?, updated_at = ? WHERE id = ? AND deleted_at IS NULL",
            (now_iso(), now_iso(), project_id),
        )
    if cur.rowcount == 0:
        return error_response(404, "not_found", "Project not found", request.state.request_id)
    return Response(status_code=204)


@app.post(f"{API_PREFIX}/projects/{{project_id}}/restore", status_code=204)
def restore_project(project_id: str, request: Request, _: None = Depends(require_auth)):
    with conn() as c:
        cur = c.execute(
            "UPDATE projects SET status = 'active', archived_at = NULL, updated_at = ? WHERE id = ? AND deleted_at IS NULL",
            (now_iso(), project_id),
        )
    if cur.rowcount == 0:
        return error_response(404, "not_found", "Project not found", request.state.request_id)
    return Response(status_code=204)


@app.get(f"{API_PREFIX}/tasks")
def list_tasks(
    request: Request,
    _: None = Depends(require_auth),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = None,
    project_id: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    assignee_id: str | None = None,
    tag: str | None = None,
    q: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    allowed_sort = {"created_at", "updated_at", "due_date", "priority"}
    if sort_by not in allowed_sort:
        return error_response(400, "invalid_sort", f"Invalid sort_by. Allowed: {sorted(allowed_sort)}", request.state.request_id)
    if sort_order not in {"asc", "desc"}:
        return error_response(400, "invalid_sort", "sort_order must be asc or desc", request.state.request_id)

    offset = decode_cursor(cursor)
    clauses = ["t.deleted_at IS NULL"]
    params: list[Any] = []
    joins = ""
    if project_id:
        clauses.append("t.project_id = ?")
        params.append(project_id)
    if status:
        clauses.append("t.status = ?")
        params.append(status)
    if priority:
        clauses.append("t.priority = ?")
        params.append(priority)
    if assignee_id:
        clauses.append("t.assignee_id = ?")
        params.append(assignee_id)
    if q:
        clauses.append("(t.title LIKE ? OR t.description LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])
    if tag:
        joins += " JOIN task_tags tt ON tt.task_id = t.id JOIN tags tg ON tg.id = tt.tag_id "
        clauses.append("tg.slug = ?")
        params.append(tag)

    where_sql = " AND ".join(clauses)
    sql = f"SELECT DISTINCT t.* FROM tasks t {joins} WHERE {where_sql} ORDER BY t.{sort_by} {sort_order.upper()} LIMIT ? OFFSET ?"
    with conn() as c:
        rows = [row_to_dict(r) for r in c.execute(sql, (*params, limit + 1, offset)).fetchall()]
    return list_response(rows, limit, offset)


@app.post(f"{API_PREFIX}/tasks", status_code=201)
def create_task(request: Request, payload: dict[str, Any], _: None = Depends(require_auth)):
    tid = str(uuid.uuid4())
    created = now_iso()
    with conn() as c:
        c.execute(
            "INSERT INTO tasks(id,project_id,title,description,status,priority,assignee_id,due_date,created_at,updated_at,completed_at,deleted_at) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",
            (
                tid,
                payload.get("project_id", str(uuid.uuid4())),
                payload.get("title", "Untitled task"),
                payload.get("description"),
                payload.get("status", "todo"),
                payload.get("priority", "medium"),
                payload.get("assignee_id"),
                payload.get("due_date"),
                created,
                created,
                None,
                None,
            ),
        )
        row = c.execute("SELECT * FROM tasks WHERE id = ?", (tid,)).fetchone()
    return row_to_dict(row)


@app.get(f"{API_PREFIX}/tasks/{{task_id}}")
def get_task(task_id: str, request: Request, _: None = Depends(require_auth)):
    with conn() as c:
        row = c.execute("SELECT * FROM tasks WHERE id = ? AND deleted_at IS NULL", (task_id,)).fetchone()
    if not row:
        return error_response(404, "not_found", "Task not found", request.state.request_id)
    return row_to_dict(row)


@app.patch(f"{API_PREFIX}/tasks/{{task_id}}")
def patch_task(task_id: str, payload: dict[str, Any], request: Request, _: None = Depends(require_auth)):
    allowed = {"title", "description", "status", "priority", "assignee_id", "due_date"}
    updates = {k: v for k, v in payload.items() if k in allowed}
    if not updates:
        return error_response(400, "invalid_request", "No updatable fields provided", request.state.request_id)
    set_sql = ", ".join([f"{k} = ?" for k in updates.keys()] + ["updated_at = ?"])
    params = list(updates.values()) + [now_iso(), task_id]
    with conn() as c:
        cur = c.execute(f"UPDATE tasks SET {set_sql} WHERE id = ? AND deleted_at IS NULL", params)
        if cur.rowcount == 0:
            return error_response(404, "not_found", "Task not found", request.state.request_id)
        row = c.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
    return row_to_dict(row)


@app.delete(f"{API_PREFIX}/tasks/{{task_id}}", status_code=204)
def delete_task(task_id: str, request: Request, _: None = Depends(require_auth)):
    with conn() as c:
        cur = c.execute("UPDATE tasks SET deleted_at = ?, updated_at = ? WHERE id = ? AND deleted_at IS NULL", (now_iso(), now_iso(), task_id))
    if cur.rowcount == 0:
        return error_response(404, "not_found", "Task not found", request.state.request_id)
    return Response(status_code=204)


@app.post(f"{API_PREFIX}/tasks/{{task_id}}/complete", status_code=204)
def complete_task(task_id: str, request: Request, _: None = Depends(require_auth)):
    with conn() as c:
        cur = c.execute(
            "UPDATE tasks SET status = 'done', completed_at = ?, updated_at = ? WHERE id = ? AND deleted_at IS NULL",
            (now_iso(), now_iso(), task_id),
        )
    if cur.rowcount == 0:
        return error_response(404, "not_found", "Task not found", request.state.request_id)
    return Response(status_code=204)


@app.post(f"{API_PREFIX}/tasks/{{task_id}}/reopen", status_code=204)
def reopen_task(task_id: str, request: Request, _: None = Depends(require_auth)):
    with conn() as c:
        cur = c.execute(
            "UPDATE tasks SET status = 'in_progress', completed_at = NULL, updated_at = ? WHERE id = ? AND deleted_at IS NULL",
            (now_iso(), task_id),
        )
    if cur.rowcount == 0:
        return error_response(404, "not_found", "Task not found", request.state.request_id)
    return Response(status_code=204)


@app.get(f"{API_PREFIX}/tasks/{{task_id}}/comments")
def list_comments(task_id: str, request: Request, _: None = Depends(require_auth), limit: int = Query(default=20, ge=1, le=100), cursor: str | None = None):
    offset = decode_cursor(cursor)
    with conn() as c:
        rows = [
            row_to_dict(r)
            for r in c.execute(
                "SELECT * FROM comments WHERE task_id = ? ORDER BY created_at ASC LIMIT ? OFFSET ?",
                (task_id, limit + 1, offset),
            ).fetchall()
        ]
    return list_response(rows, limit, offset)


@app.post(f"{API_PREFIX}/tasks/{{task_id}}/comments", status_code=201)
def create_comment(task_id: str, payload: dict[str, Any], _: None = Depends(require_auth)):
    cid = str(uuid.uuid4())
    created = now_iso()
    with conn() as c:
        c.execute(
            "INSERT INTO comments(id,task_id,author_id,body,created_at,updated_at) VALUES(?,?,?,?,?,?)",
            (cid, task_id, payload.get("author_id", str(uuid.uuid4())), payload.get("body", ""), created, created),
        )
        row = c.execute("SELECT * FROM comments WHERE id = ?", (cid,)).fetchone()
    return row_to_dict(row)


@app.get(f"{API_PREFIX}/comments/{{comment_id}}")
def get_comment(comment_id: str, request: Request, _: None = Depends(require_auth)):
    with conn() as c:
        row = c.execute("SELECT * FROM comments WHERE id = ?", (comment_id,)).fetchone()
    if not row:
        return error_response(404, "not_found", "Comment not found", request.state.request_id)
    return row_to_dict(row)


@app.patch(f"{API_PREFIX}/comments/{{comment_id}}")
def patch_comment(comment_id: str, payload: dict[str, Any], request: Request, _: None = Depends(require_auth)):
    body = payload.get("body")
    if body is None:
        return error_response(400, "invalid_request", "body is required", request.state.request_id)
    with conn() as c:
        cur = c.execute("UPDATE comments SET body = ?, updated_at = ? WHERE id = ?", (body, now_iso(), comment_id))
        if cur.rowcount == 0:
            return error_response(404, "not_found", "Comment not found", request.state.request_id)
        row = c.execute("SELECT * FROM comments WHERE id = ?", (comment_id,)).fetchone()
    return row_to_dict(row)


@app.delete(f"{API_PREFIX}/comments/{{comment_id}}", status_code=204)
def delete_comment(comment_id: str, request: Request, _: None = Depends(require_auth)):
    with conn() as c:
        cur = c.execute("DELETE FROM comments WHERE id = ?", (comment_id,))
    if cur.rowcount == 0:
        return error_response(404, "not_found", "Comment not found", request.state.request_id)
    return Response(status_code=204)


@app.get(f"{API_PREFIX}/tags")
def list_tags(request: Request, _: None = Depends(require_auth), limit: int = Query(default=20, ge=1, le=100), cursor: str | None = None, q: str | None = None):
    offset = decode_cursor(cursor)
    params: list[Any] = []
    where = ""
    if q:
        where = "WHERE name LIKE ?"
        params.append(f"%{q}%")
    with conn() as c:
        rows = [
            row_to_dict(r)
            for r in c.execute(
                f"SELECT * FROM tags {where} ORDER BY name ASC LIMIT ? OFFSET ?",
                (*params, limit + 1, offset),
            ).fetchall()
        ]
    return list_response(rows, limit, offset)


@app.post(f"{API_PREFIX}/tags", status_code=201)
def create_tag(payload: dict[str, Any], _: None = Depends(require_auth)):
    tag_id = str(uuid.uuid4())
    created = now_iso()
    with conn() as c:
        c.execute(
            "INSERT INTO tags(id,name,slug,color,created_at) VALUES(?,?,?,?,?)",
            (tag_id, payload.get("name", "Tag"), payload.get("slug", f"tag-{tag_id[:8]}"), payload.get("color", "#2563eb"), created),
        )
        row = c.execute("SELECT * FROM tags WHERE id = ?", (tag_id,)).fetchone()
    return row_to_dict(row)


@app.get(f"{API_PREFIX}/tags/{{tag_id}}")
def get_tag(tag_id: str, request: Request, _: None = Depends(require_auth)):
    with conn() as c:
        row = c.execute("SELECT * FROM tags WHERE id = ?", (tag_id,)).fetchone()
    if not row:
        return error_response(404, "not_found", "Tag not found", request.state.request_id)
    return row_to_dict(row)


@app.patch(f"{API_PREFIX}/tags/{{tag_id}}")
def patch_tag(tag_id: str, payload: dict[str, Any], request: Request, _: None = Depends(require_auth)):
    allowed = {"name", "slug", "color"}
    updates = {k: v for k, v in payload.items() if k in allowed}
    if not updates:
        return error_response(400, "invalid_request", "No updatable fields provided", request.state.request_id)
    set_sql = ", ".join([f"{k} = ?" for k in updates.keys()])
    params = list(updates.values()) + [tag_id]
    with conn() as c:
        cur = c.execute(f"UPDATE tags SET {set_sql} WHERE id = ?", params)
        if cur.rowcount == 0:
            return error_response(404, "not_found", "Tag not found", request.state.request_id)
        row = c.execute("SELECT * FROM tags WHERE id = ?", (tag_id,)).fetchone()
    return row_to_dict(row)


@app.delete(f"{API_PREFIX}/tags/{{tag_id}}", status_code=204)
def delete_tag(tag_id: str, request: Request, _: None = Depends(require_auth)):
    with conn() as c:
        c.execute("DELETE FROM task_tags WHERE tag_id = ?", (tag_id,))
        cur = c.execute("DELETE FROM tags WHERE id = ?", (tag_id,))
    if cur.rowcount == 0:
        return error_response(404, "not_found", "Tag not found", request.state.request_id)
    return Response(status_code=204)


@app.post(f"{API_PREFIX}/tasks/{{task_id}}/tags/{{tag_id}}", status_code=204)
def attach_tag(task_id: str, tag_id: str, request: Request, _: None = Depends(require_auth)):
    with conn() as c:
        c.execute("INSERT OR IGNORE INTO task_tags(task_id,tag_id) VALUES(?,?)", (task_id, tag_id))
    return Response(status_code=204)


@app.delete(f"{API_PREFIX}/tasks/{{task_id}}/tags/{{tag_id}}", status_code=204)
def detach_tag(task_id: str, tag_id: str, request: Request, _: None = Depends(require_auth)):
    with conn() as c:
        c.execute("DELETE FROM task_tags WHERE task_id = ? AND tag_id = ?", (task_id, tag_id))
    return Response(status_code=204)


@app.get(f"{API_PREFIX}/users/me")
def get_me(request: Request, _: None = Depends(require_auth)):
    with conn() as c:
        row = c.execute("SELECT * FROM users ORDER BY created_at ASC LIMIT 1").fetchone()
    return row_to_dict(row)


@app.get(f"{API_PREFIX}/users")
def list_users(
    request: Request,
    _: None = Depends(require_auth),
    limit: int = Query(default=20, ge=1, le=100),
    cursor: str | None = None,
    role: str | None = None,
    status: str | None = None,
    q: str | None = None,
    sort_by: str = "created_at",
    sort_order: str = "desc",
):
    allowed_sort = {"created_at", "full_name", "email"}
    if sort_by not in allowed_sort:
        return error_response(400, "invalid_sort", f"Invalid sort_by. Allowed: {sorted(allowed_sort)}", request.state.request_id)
    if sort_order not in {"asc", "desc"}:
        return error_response(400, "invalid_sort", "sort_order must be asc or desc", request.state.request_id)

    offset = decode_cursor(cursor)
    clauses = ["1=1"]
    params: list[Any] = []
    if role:
        clauses.append("role = ?")
        params.append(role)
    if status:
        clauses.append("status = ?")
        params.append(status)
    if q:
        clauses.append("(email LIKE ? OR full_name LIKE ?)")
        params.extend([f"%{q}%", f"%{q}%"])
    where_sql = " AND ".join(clauses)
    with conn() as c:
        rows = [
            row_to_dict(r)
            for r in c.execute(
                f"SELECT * FROM users WHERE {where_sql} ORDER BY {sort_by} {sort_order.upper()} LIMIT ? OFFSET ?",
                (*params, limit + 1, offset),
            ).fetchall()
        ]
    return list_response(rows, limit, offset)


@app.get(f"{API_PREFIX}/users/{{user_id}}")
def get_user(user_id: str, request: Request, _: None = Depends(require_auth)):
    with conn() as c:
        row = c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    if not row:
        return error_response(404, "not_found", "User not found", request.state.request_id)
    return row_to_dict(row)


@app.patch(f"{API_PREFIX}/users/{{user_id}}")
def patch_user(user_id: str, payload: dict[str, Any], request: Request, _: None = Depends(require_auth)):
    allowed = {"full_name", "role", "status"}
    updates = {k: v for k, v in payload.items() if k in allowed}
    if not updates:
        return error_response(400, "invalid_request", "No updatable fields provided", request.state.request_id)
    set_sql = ", ".join([f"{k} = ?" for k in updates.keys()])
    params = list(updates.values()) + [user_id]
    with conn() as c:
        cur = c.execute(f"UPDATE users SET {set_sql} WHERE id = ?", params)
        if cur.rowcount == 0:
            return error_response(404, "not_found", "User not found", request.state.request_id)
        row = c.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return row_to_dict(row)


@app.get(f"{API_PREFIX}/users/{{user_id}}/tasks")
def list_user_tasks(user_id: str, request: Request, _: None = Depends(require_auth), limit: int = Query(default=20, ge=1, le=100), cursor: str | None = None):
    offset = decode_cursor(cursor)
    with conn() as c:
        rows = [
            row_to_dict(r)
            for r in c.execute(
                "SELECT * FROM tasks WHERE assignee_id = ? AND deleted_at IS NULL ORDER BY created_at DESC LIMIT ? OFFSET ?",
                (user_id, limit + 1, offset),
            ).fetchall()
        ]
    return list_response(rows, limit, offset)
