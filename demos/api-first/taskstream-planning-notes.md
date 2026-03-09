# API planning notes (for OpenAPI authoring)

Project: **TaskStream** (SaaS for project and task management)
API version: **v1**
Base URL: `https://api.taskstream.example.com/v1`
Planning date: 2026-03-09
Status: Draft for OpenAPI writing

## 1. API goals

- Provide full CRUD for projects, tasks, comments, tags, and users.
- Support list endpoints with pagination, filtering, and sorting.
- Ship a stable contract for web, mobile, and partner integrations.

## 2. Global conventions

- Content type: `application/json; charset=utf-8`.
- Date-time format: ISO 8601 UTC (`2026-03-09T10:22:31Z`).
- IDs: UUID v4 strings.
- Auth: Bearer JWT (`Authorization: Bearer <token>`).
- Versioning: URI versioning (`/v1`).
- Idempotency: support `Idempotency-Key` for `POST /projects` and `POST /tasks`.
- Deletion model: soft delete by default (`deleted_at`), hard delete for admins only.
- Correlation: accept `X-Request-Id`; generate and return one if missing.

## 3. List endpoint standards

- Pagination: cursor-based.
- Query params: `limit` (1..100, default 20), `cursor` (opaque string).
- Standard list response:
  - `data`: array of resources
  - `page.next_cursor`: string or `null`
  - `page.has_more`: boolean
- Filtering: query params (`status`, `assignee_id`, `created_from`, etc.).
- Sorting: `sort_by` + `sort_order`.
- `sort_order`: `asc | desc`.
- If `sort_by` is omitted, use resource default.

## 4. Resources and methods

### 4.1 Projects

- `GET /projects` - list projects (pagination/filter/sort).
- `POST /projects` - create project.
- `GET /projects/{project_id}` - get project.
- `PATCH /projects/{project_id}` - partial update.
- `DELETE /projects/{project_id}` - soft delete.
- `POST /projects/{project_id}/archive` - archive project.
- `POST /projects/{project_id}/restore` - restore archived project.

Filters for `GET /projects`:

- `status`: `active | archived`
- `owner_id`: UUID
- `created_from`, `created_to`: datetime
- `q`: full-text on `name`, `description`

Sorting for `GET /projects`:

- `sort_by`: `created_at | updated_at | name`
- default: `updated_at desc`

### 4.2 Tasks

- `GET /tasks` - list tasks.
- `POST /tasks` - create task.
- `GET /tasks/{task_id}` - get task.
- `PATCH /tasks/{task_id}` - update task.
- `DELETE /tasks/{task_id}` - soft delete.
- `POST /tasks/{task_id}/complete` - mark complete.
- `POST /tasks/{task_id}/reopen` - reopen task.

Filters for `GET /tasks`:

- `project_id`: UUID
- `status`: `todo | in_progress | done | blocked`
- `priority`: `low | medium | high | urgent`
- `assignee_id`: UUID
- `due_from`, `due_to`: date
- `created_from`, `created_to`: datetime
- `tag`: string (slug)
- `q`: full-text on `title`, `description`

Sorting for `GET /tasks`:

- `sort_by`: `created_at | updated_at | due_date | priority`
- default: `created_at desc`

### 4.3 Comments

- `GET /tasks/{task_id}/comments` - list task comments.
- `POST /tasks/{task_id}/comments` - create comment.
- `GET /comments/{comment_id}` - get comment.
- `PATCH /comments/{comment_id}` - update comment.
- `DELETE /comments/{comment_id}` - delete comment.

Filters for `GET /tasks/{task_id}/comments`:

- `author_id`: UUID
- `created_from`, `created_to`: datetime

Sorting:

- `sort_by`: `created_at`
- default: `created_at asc`

### 4.4 Tags

- `GET /tags` - list tags.
- `POST /tags` - create tag.
- `GET /tags/{tag_id}` - get tag.
- `PATCH /tags/{tag_id}` - update tag.
- `DELETE /tags/{tag_id}` - delete tag.
- `POST /tasks/{task_id}/tags/{tag_id}` - attach tag to task.
- `DELETE /tasks/{task_id}/tags/{tag_id}` - detach tag from task.

Filters for `GET /tags`:

- `q`: tag name search

Sorting:

- `sort_by`: `name | created_at`
- default: `name asc`

### 4.5 Users

- `GET /users/me` - current user profile.
- `GET /users` - list workspace users.
- `GET /users/{user_id}` - get user profile.
- `PATCH /users/{user_id}` - update profile (role-restricted).
- `GET /users/{user_id}/tasks` - list user tasks.

Filters for `GET /users`:

- `role`: `admin | manager | member | guest`
- `status`: `active | invited | suspended`
- `q`: search by email/full name

Sorting:

- `sort_by`: `created_at | full_name | email`
- default: `created_at desc`

## 5. Draft schema inventory

- `Project`: `id`, `name`, `description`, `status`, `owner_id`, `created_at`, `updated_at`, `archived_at`.
- `Task`: `id`, `project_id`, `title`, `description`, `status`, `priority`, `assignee_id`, `due_date`, `created_at`, `updated_at`, `completed_at`.
- `Comment`: `id`, `task_id`, `author_id`, `body`, `created_at`, `updated_at`.
- `Tag`: `id`, `name`, `slug`, `color`, `created_at`.
- `User`: `id`, `email`, `full_name`, `role`, `status`, `created_at`.
- `Error`: `error.code`, `error.message`, `error.details`, `request_id`.

## 6. Response status codes

- `200 OK` - successful GET/PATCH.
- `201 Created` - successful POST.
- `204 No Content` - successful DELETE/archive/restore with no body.
- `400 Bad Request` - invalid query/body format.
- `401 Unauthorized` - missing/invalid token.
- `403 Forbidden` - insufficient permissions.
- `404 Not Found` - resource missing.
- `409 Conflict` - state conflict/idempotency conflict.
- `422 Unprocessable Entity` - business validation failure.
- `429 Too Many Requests` - rate limit exceeded.
- `500 Internal Server Error` - unexpected error.

## 7. Error and validation rules

- Use one standard error envelope for all endpoints.
- Validation errors must include array items with `field`, `message`, `rule`.
- Invalid `sort_by` or enum filter values return `400` with allowed values.

## 8. Security and access

- Scope model:
  - `projects:read`, `projects:write`
  - `tasks:read`, `tasks:write`
  - `comments:write`
  - `users:read`
- Role matrix is maintained in a separate access-control doc and referenced from OpenAPI `securitySchemes` and operation descriptions.

## 9. Non-functional constraints

- Rate limit: 600 req/min per token, burst 120.
- Max list `limit`: 100.
- API timeout: 15 seconds.
- Max comment body: 20 KB.
- Max project/task description body: 64 KB.

## 10. OpenAPI Definition of Done (v1)

- All endpoints above are documented.
- Every list endpoint includes pagination + filters + sorting.
- Each operation includes at least 1 request example and 1 response example.
- All 4xx/5xx responses are defined via shared `Error` schema.
- `securitySchemes` (BearerAuth) and operation-level security are specified.
- `operationId`, `tags`, `summary`, and `description` are present.
- Reusable components are defined in `components/schemas`, `components/parameters`, `components/responses`.

## 11. Open questions before final spec freeze

- Do we need bulk task updates (`PATCH /tasks/bulk`) in v1?
- Do we support `include` expansions (`include=project,assignee`) in v1?
- Confirm hard-delete policy for compliance workflows.
- Confirm webhook SLA requirements if webhooks are included in v1.
