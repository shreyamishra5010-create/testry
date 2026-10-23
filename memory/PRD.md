# Northstar Task Board PRD

## Original problem statement
Build a simplified Kanban-style task management system inspired by Trello/Jira with email/password authentication, boards, default columns, task CRUD, drag-and-drop movement, members, comments, search/filtering, sample data, API documentation, and testing.

## User decisions
- Node.js/Express backend with SQLite database
- Email/password login with JWT
- Column deletion offers moving tasks to To Do or deleting tasks
- Clean, bright Trello-like visual direction
- Seed sample board and tasks

## Architecture decisions
- Express API on port 8001 with SQLite foreign keys and parameterized queries
- bcryptjs hashes passwords; jsonwebtoken protects API routes
- React frontend uses the configured `REACT_APP_BACKEND_URL`
- Integer task positions are persisted and updated during moves
- Board membership is checked server-side for all board/task/comment/member operations

## Personas
- Individual planner who needs a lightweight personal board
- Small product team coordinating work across stages
- Board owner managing collaborators and task visibility

## Core requirements (static)
- Auth: register, login, logout, protected API access
- Boards: list, create, open, delete/rename API support, default columns
- Columns: add, rename, delete with task policy
- Tasks: create, edit, delete, priorities, due dates, drag/drop movement
- Collaboration: members, comments, own-comment deletion
- Discovery: keyword search, priority filter, reset
- Documentation and seeded demo account

## Implemented — 2026-10-23
- Replaced the starter API with Node.js/Express + SQLite schema and automatic seed data
- Added JWT email/password auth, bcrypt password hashing, board authorization, and REST endpoints
- Built bright Northstar dashboard and responsive Kanban workspace with test IDs
- Added board creation, task modal, task editing/deleting, filters, priority labels, due dates, drag/drop, comments, members, and column policy controls
- Added README, schema/seed notes, and demo credentials
- Verified preview login, dashboard, board rendering, protected 401/200 API behavior, editing, column modal, comments, and responsive layout

## Prioritized backlog
- P0: Keep core board/task/member/comment flows stable
- P1: Add explicit board rename/delete controls to the dashboard UI
- P1: Add assignee picker UI and member removal controls
- P2: Add column reordering and richer activity history
- P2: Add Postman collection and ER diagram asset

## Next tasks
1. Add assignee selection and member management panel.
2. Add board settings for rename/delete from the dashboard.
3. Add column reordering with persistent positions.
4. Add API collection and visual ER diagram documentation.