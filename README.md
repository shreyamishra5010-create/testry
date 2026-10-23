# Northstar Task Board

Bright, simplified Kanban workspace inspired by Trello and Jira. The backend is Node.js/Express with SQLite, JWT authentication, bcrypt password hashing, and parameterized SQL. The frontend is React.

## Demo
`demo@taskboard.local` / `demo1234`

## Run
Install backend dependencies with `cd backend && yarn install`, then start it with `yarn start`. The existing frontend uses `REACT_APP_BACKEND_URL` and runs with `cd frontend && yarn start`.

## API summary
Auth: `POST /api/auth/register`, `POST /api/auth/login`, `GET /api/me`
Boards: `GET/POST /api/boards`, `GET/PATCH/DELETE /api/boards/:id`
Columns: `POST /api/boards/:id/columns`, `PATCH/DELETE /api/columns/:id`
Tasks: `POST /api/boards/:id/tasks`, `PATCH/DELETE /api/tasks/:id`, `PATCH /api/tasks/:id/move`
Comments: `GET/POST /api/tasks/:id/comments`, `DELETE /api/comments/:id`
Members: `POST /api/boards/:id/members`, `DELETE /api/boards/:id/members/:userId`

Cards use integer positions and board access is enforced server-side. Column deletion offers moving tasks to To Do or deleting tasks.
