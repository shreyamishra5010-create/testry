-- Demo data. Runs automatically only when the users table is empty.
-- Both demo passwords are "demo1234" (bcrypt hash below).
INSERT INTO users (id, name, email, password_hash, created_at) VALUES
  (1, 'Alex Morgan', 'demo@taskboard.local', '$2a$10$hrIhGPRBI/5a9v3sEJSKgeqX4rgOx6SvMYonFhzuPxtqQ03Y7vBUq', '2026-06-01T09:00:00.000Z'),
  (2, 'Jordan Lee', 'jordan@taskboard.local', '$2a$10$hrIhGPRBI/5a9v3sEJSKgeqX4rgOx6SvMYonFhzuPxtqQ03Y7vBUq', '2026-06-01T09:05:00.000Z');

INSERT INTO boards (id, name, description, owner_id, created_at) VALUES
  (1, 'Product Launch', 'Coordinate the next release from idea to shipped.', 1, '2026-06-01T09:10:00.000Z');

INSERT INTO board_members (board_id, user_id, role) VALUES
  (1, 1, 'owner'),
  (1, 2, 'member');

INSERT INTO columns (id, board_id, name, position, color) VALUES
  (1, 1, 'To Do', 0, '#0052CC'),
  (2, 1, 'In Progress', 1, '#FFAB00'),
  (3, 1, 'Done', 2, '#00875A');

INSERT INTO tasks (id, board_id, column_id, title, description, priority, due_date, assignee_id, position, created_by, created_at, updated_at) VALUES
  (1, 1, 1, 'Audit onboarding flow', 'Review activation drop-offs and list the top three fixes.', 'high', '2026-07-03', 1, 0, 1, '2026-06-01T09:20:00.000Z', '2026-06-01T09:20:00.000Z'),
  (2, 1, 1, 'Draft pricing FAQ', 'Answer the ten most common billing questions from support.', 'medium', '2026-07-10', 2, 1, 1, '2026-06-01T09:21:00.000Z', '2026-06-01T09:21:00.000Z'),
  (3, 1, 1, 'Collect beta testimonials', 'Reach out to five beta customers for short quotes.', 'low', NULL, NULL, 2, 1, '2026-06-01T09:22:00.000Z', '2026-06-01T09:22:00.000Z'),
  (4, 1, 2, 'Design release notes', 'Draft the customer-facing release story with screenshots.', 'medium', '2026-07-01', 2, 0, 1, '2026-06-01T09:23:00.000Z', '2026-06-01T09:23:00.000Z'),
  (5, 1, 2, 'Fix checkout validation', 'Card errors are shown twice on mobile Safari.', 'high', '2026-06-28', 1, 1, 2, '2026-06-01T09:24:00.000Z', '2026-06-01T09:24:00.000Z'),
  (6, 1, 3, 'QA regression pass', 'Run the smoke test across the new workspace experience.', 'low', NULL, 2, 0, 1, '2026-06-01T09:25:00.000Z', '2026-06-01T09:25:00.000Z');

INSERT INTO comments (task_id, user_id, body, created_at) VALUES
  (1, 2, 'I pulled the funnel numbers, step 3 loses 40% of new users.', '2026-06-02T10:00:00.000Z'),
  (1, 1, 'Great, let''s start there. I will share fixes by Friday.', '2026-06-02T10:30:00.000Z'),
  (5, 2, 'Reproduced on iOS 19, looking into it.', '2026-06-03T14:00:00.000Z');
