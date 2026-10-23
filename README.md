# Northstar Task Board

A simplified Trello/Jira-style Kanban tool. Teams create boards, organize work into columns, and drag tasks between them. Every change is saved and protected by board membership.

**Stack:** React (CRA + CRACO) · Node.js / Express · SQLite (`sqlite3`) · JWT auth · bcrypt password hashing · parameterized SQL everywhere.

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
# backend (API on API_PORT, e.g. 8002)
cd backend
yarn install
# .env needs: JWT_SECRET=<random string>  API_PORT=8002
yarn start

# frontend
cd frontend
yarn install
# .env needs: REACT_APP_BACKEND_URL=http://localhost:8002
yarn start
```
The schema (`backend/schema.sql`) is applied on every start (idempotent). Seed data (`backend/seed.sql`) is loaded only when the database has no users.

**Reset the demo data:** stop the API, delete `backend/taskboard.sqlite`, start again.

> On the Emergent preview, supervisor starts `backend/server.py`, a tiny launcher that boots `node server.js` and forwards `/api` traffic to it. The app logic lives entirely in Node.

## Project layout
```
backend/
  server.js            Express app wiring
  server.py            Platform launcher (starts Node, proxies requests)
  schema.sql, seed.sql Database schema and demo data
  src/db.js            SQLite connection, query helpers, schema/seed bootstrap
  src/auth.js          JWT sign / requireAuth middleware
  src/access.js        Membership checks, board payload, task ordering
  src/routes/          auth, boards (+members, columns create), columns, tasks (+comments), comments
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
- **Validation:** required titles/names, priority enum, email format, 8+ character passwords, duplicate email → `409`, assignee must be a member, target column must belong to the same board.

## Docs
- ER diagram: [`docs/ER_DIAGRAM.md`](docs/ER_DIAGRAM.md)
- API reference: [`docs/API.md`](docs/API.md)
- Postman collection: [`docs/postman_collection.json`](docs/postman_collection.json)
