# Northstar Task Board — PRD

## Original problem
Simplified Trello/Jira Kanban tool: email/password JWT auth, boards (default To Do/In Progress/Done) with owner/member access, columns CRUD, tasks (priority, due date, assignee), drag & drop with persisted positions + accessible fallback, comments, search/filters, bright Trello-like UI with sample data, and docs (README, schema/seed SQL, ER diagram, API docs/Postman).

## User choices
Node.js/Express + SQLite · email/password · deleting a column deletes its tasks · bright Trello-like look · sample data included.

## Architecture
- backend/server.js (Express) + src/{db,auth,access}.js + src/routes/*; schema.sql/seed.sql loaded on start
- backend/server.py = platform launcher (spawns Node on API_PORT, proxies /api from 8001)
- frontend: App.js routes; pages/{Auth,Dashboard,Board}Page; components/board/*; lib/api.js
- docs/: ER_DIAGRAM.md, API.md, postman_collection.json

## Implemented
- Session 1: MVP (auth, boards, columns, tasks, comments, filters, UI, seed)
- 2026-06: Modular refactor (frontend + backend) with the same look; durable startup through supervisor
- 2026-06: Dense position reordering (within and across columns), card top/bottom-half drop, self-drop fix, optimistic UI
- 2026-06: Assignee field + filter, members modal (invite/remove), board settings (rename/delete), column delete cascades tasks
- 2026-06: Validation (email, password, priority, due date, assignee membership, same-board column), 404 vs 403, own-comment delete by user id
- 2026-06: README, schema.sql, seed.sql, ER diagram, API reference, Postman collection, test credentials
- Testing: iteration_2: backend 27/27; frontend all flows pass; follow-up bugs fixed and verified

## Backlog
- P1: Column reordering (drag columns)
- P2: Activity log per board, member avatars with colors, mobile touch drag, 100+ task performance check
