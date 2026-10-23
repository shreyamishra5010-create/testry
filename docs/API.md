# API Reference

Base URL: `{BASE}/api`. All bodies are JSON. Protected routes need `Authorization: Bearer <token>`.
Errors always look like `{ "error": "message" }`.

| Status | Meaning |
|---|---|
| 400 | Validation failed |
| 401 | Missing / invalid token, or wrong login |
| 403 | Not a board member, or owner-only action |
| 404 | Board, column, task, comment, or invited user not found |
| 409 | Email already registered |

## Auth
| Method | Path | Body | Returns |
|---|---|---|---|
| POST | `/auth/register` | `{name, email, password(8+)}` | `201 {token, user}` |
| POST | `/auth/login` | `{email, password}` | `{token, user}` |
| GET | `/me` | – | `{user}` |

## Boards
| Method | Path | Body | Notes |
|---|---|---|---|
| GET | `/boards` | – | Boards you belong to, with `role`, `task_count`, `due_soon`, `member_count` |
| POST | `/boards` | `{name, description?}` | Creates To Do / In Progress / Done. Returns full board |
| GET | `/boards/:id` | – | Board + `columns[].tasks[]` (ordered) + `members[]` |
| PATCH | `/boards/:id` | `{name?, description?}` | Owner only |
| DELETE | `/boards/:id` | – | Owner only, cascades everything |

## Members
| Method | Path | Body | Notes |
|---|---|---|---|
| POST | `/boards/:id/members` | `{email}` | Owner only; user must already be registered. Returns board |
| DELETE | `/boards/:id/members/:userId` | – | Owner only; owner can't be removed. Clears their assignments |

## Columns
| Method | Path | Body | Notes |
|---|---|---|---|
| POST | `/boards/:id/columns` | `{name, color?}` | Appended at the end |
| PATCH | `/columns/:id` | `{name}` | Rename |
| PATCH | `/columns/:id/move` | `{position}` | 0-based index among the board's columns; renumbers densely. Returns ordered columns |
| DELETE | `/columns/:id` | – | **Deletes the column and its tasks.** Returns `{ok, deleted_tasks}` |

## Tasks
| Method | Path | Body | Notes |
|---|---|---|---|
| POST | `/boards/:id/tasks` | `{column_id, title, description?, priority?, due_date?, assignee_id?}` | Added to bottom of column |
| PATCH | `/tasks/:id` | any of `{title, description, priority, due_date, assignee_id, column_id}` | Changing `column_id` moves it to the bottom of that column |
| PATCH | `/tasks/:id/move` | `{column_id, position}` | `position` = 0-based index in target column (excluding the moved task). Renumbers both columns |
| DELETE | `/tasks/:id` | – | |

`priority` ∈ `low | medium | high`. `due_date` must be `YYYY-MM-DD` (validated). `assignee_id` must be a board member (or `null`).

## Comments
| Method | Path | Body | Notes |
|---|---|---|---|
| GET | `/tasks/:id/comments` | – | Oldest first, includes `author_name` |
| POST | `/tasks/:id/comments` | `{body}` | |
| DELETE | `/comments/:id` | – | Author only |

## Activity
| Method | Path | Notes |
|---|---|---|
| GET | `/boards/:id/activity?limit=50` | Newest first (max 200). Each item: `{id, action, message, user_id, user_name, created_at}` |

Recorded actions: `task.created`, `task.updated` (lists changed fields), `task.moved`, `task.reordered`, `task.deleted`, `column.added`, `column.renamed`, `column.moved`, `column.deleted`, `comment.added`. Member changes are not logged.

## Health
`GET /health` → `{ok: true, service: "task-board-api"}`
