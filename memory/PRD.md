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

- 2026-06: Column reordering: drag a column by its header (left/right half), or use Move left/right in column settings; PATCH /api/columns/:id/move with dense positions
- 2026-06: Activity feed: `activity` table, a side panel opened by the Activity button, GET /api/boards/:id/activity. Logs task create/edit (changed fields only)/move/reorder/delete, column add/rename/move/delete, and comment added. Member changes are not logged, as the user chose
- 2026-06: Escape closes modals and the panel; edit plus invalid column is now validated before saving
- Testing: iteration_3 found 3 minor backend edge cases and an Escape-key UI gap, all fixed. The full backend test suite (43 tests) then passed. The UI fixes were checked by a build and code review only, with no browser re-run

- 2026-06: Touch dragging (hooks/useTouchDrag.js): press and hold (350ms) on cards or column headers, floating ghost, edge auto-scroll, swipe and tap still work normally, HTML5 drag disabled on coarse pointers. iteration_4: 8/8 passed

## Backlog
- P2: Drop-position indicator line while dragging, member avatars with colors, due-soon highlights, 100+ task performance check
