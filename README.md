# Northstar Task Board

A simplified Trello/Jira-style Kanban tool. Teams create boards, organize work into columns, and drag tasks between them. Every change is saved and protected by board membership.

**Stack:** React (CRA + CRACO) · Python FastAPI · MongoDB (motor) · JWT auth · bcrypt password hashing.

> The API was first built on Node.js/Express + SQLite. It was ported to FastAPI + MongoDB so it runs on the production hosting (Python runtime with a managed MongoDB). The API contract did not change.

## Demo accounts
| Email | Password | Role on "Product Launch" |
|---|---|---|
| `demo@taskboard.local` | `demo1234` | Owner |
| `jordan@taskboard.local` | `demo1234` | Member |

## Features
- Register / sign in / sign out (JWT, 7-day expiry, bcrypt hashes)
- Boards: create (auto-adds To Do / In Progress / Done), rename, edit description, delete (owner only)
- Members: owner invites registered users by email and removes them; non-members get `403`
- Columns: add, rename, reorder (drag the column header, or Move left/right in column settings), delete. **Deleting a column deletes all its tasks** (and their comments)
- Tasks: title, description, priority (low/medium/high), due date (overdue shown in red), assignee (board members only)
- Drag & drop between and within columns, saved instantly (optimistic UI, then server sync)
- Touch screens: press and hold a card or column header (~⅓ s) to drag it; a floating copy follows your finger, the board auto-scrolls near the edges, and quick swipes still scroll normally
- Keyboard/accessible move: open a task, change **Column (move task)** and save
- Comments on tasks; you can delete only your own
- Activity feed: side panel (Activity button) showing who created, edited, moved, or deleted tasks, changed columns, or commented
- Search by keyword + filter by priority and assignee (combinable, with Reset)

## Running locally
```bash
# backend
cd backend
pip install -r requirements.txt
# .env needs: MONGO_URL, DB_NAME, JWT_SECRET (long random string), CORS_ORIGINS
uvicorn server:app --port 8001 --reload

# frontend
cd frontend
yarn install
# .env needs: REACT_APP_BACKEND_URL=http://localhost:8001
yarn start
```
Indexes are created on startup. Demo data (`backend/taskboard/seed.py`) is loaded only when the database has no users.

**Reset the demo data:** drop the app's collections (`users, boards, board_members, columns, tasks, comments, activity, counters`) and restart the backend.

## Project layout
```
backend/
  server.py            FastAPI app: routers, error format, security headers, CORS
  taskboard/db.py      Mongo client, integer id counters, indexes
  taskboard/auth.py    bcrypt, JWT sign/verify, current_user, login throttling
  taskboard/access.py  Membership checks, board payload, dense ordering, activity log
  taskboard/routes/    auth, boards (+members, columns create, activity), columns, tasks (+comments)
  taskboard/seed.py    Demo data
  tests/               API test suite (pytest, runs against REACT_APP_BACKEND_URL)
frontend/src/
  App.js               Session check + routes
  lib/api.js           Fetch client, helpers, optimistic reorder
  pages/               AuthPage, DashboardPage, BoardPage
  components/          Header, Modal, board/* (column, card, modals, toolbar)
docs/
  ER_DIAGRAM.md, API.md, postman_collection.json
```

## Design decisions
- **Ordering:** tasks use dense integer positions (`0..n-1`) per column. A move removes the task, inserts it at the requested index, and renumbers both the source and target columns. Simple, always consistent, and cheap at the 100-task scale.
- **Column deletion:** deletes the column and its tasks (chosen behavior), with a confirmation that shows how many tasks will go.
- **Access control:** every board, column, task, and comment route resolves the parent board and checks `board_members`. Owner-only: edit/delete board, manage members.
- **Security:** strong random JWT secret, 7-day tokens, 8 failed logins per IP+email in 15 min → `429`, nosniff/frame-deny headers.
- **IDs:** integer ids from a `counters` collection, so the API and frontend didn't change.
- **Validation:** required titles/names, priority enum, email format, 8+ character passwords, duplicate email → `409`, assignee must be a member, target column must belong to the same board.

## Docs
- ER diagram: [`docs/ER_DIAGRAM.md`](docs/ER_DIAGRAM.md)
- API reference: [`docs/API.md`](docs/API.md)
- Postman collection: [`docs/postman_collection.json`](docs/postman_collection.json)
