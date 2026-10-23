const { get, all, run, now } = require('./db');

const h = (fn) => (req, res, next) => Promise.resolve(fn(req, res, next)).catch(next);

class HttpError extends Error {
  constructor(status, message) { super(message); this.status = status; }
}

async function membership(boardId, userId) {
  const board = await get('SELECT b.*, bm.role FROM boards b JOIN board_members bm ON bm.board_id=b.id WHERE b.id=? AND bm.user_id=?', [boardId, userId]);
  if (!board) throw new HttpError(403, 'You do not have access to this board.');
  return board;
}

async function ownerOf(boardId, userId, action) {
  const board = await membership(boardId, userId);
  if (board.owner_id !== userId) throw new HttpError(403, `Only the board owner can ${action}.`);
  return board;
}

async function loadOr404(table, id) {
  const row = await get(`SELECT * FROM ${table} WHERE id=?`, [id]);
  if (!row) throw new HttpError(404, 'Not found.');
  return row;
}

async function boardPayload(boardId) {
  const board = await get('SELECT b.*, u.name owner_name FROM boards b JOIN users u ON u.id=b.owner_id WHERE b.id=?', [boardId]);
  board.columns = await all('SELECT * FROM columns WHERE board_id=? ORDER BY position, id', [boardId]);
  const tasks = await all(`SELECT t.*, u.name assignee_name, (SELECT COUNT(*) FROM comments c WHERE c.task_id=t.id) comment_count
    FROM tasks t LEFT JOIN users u ON u.id=t.assignee_id WHERE t.board_id=? ORDER BY t.position, t.id`, [boardId]);
  for (const col of board.columns) col.tasks = tasks.filter((t) => t.column_id === col.id);
  board.members = await all('SELECT u.id,u.name,u.email,bm.role FROM board_members bm JOIN users u ON u.id=bm.user_id WHERE bm.board_id=? ORDER BY bm.role DESC, u.name', [boardId]);
  return board;
}

async function renumber(columnId) {
  const rows = await all('SELECT id FROM tasks WHERE column_id=? ORDER BY position, id', [columnId]);
  for (const [i, r] of rows.entries()) await run('UPDATE tasks SET position=? WHERE id=?', [i, r.id]);
}

// Inserts the task at `index` in the target column and renumbers both columns densely.
async function placeTask(task, columnId, index) {
  const siblings = await all('SELECT id FROM tasks WHERE column_id=? AND id<>? ORDER BY position, id', [columnId, task.id]);
  const at = Number.isInteger(index) ? Math.max(0, Math.min(index, siblings.length)) : siblings.length;
  siblings.splice(at, 0, { id: task.id });
  await run('UPDATE tasks SET column_id=?, updated_at=? WHERE id=?', [columnId, now(), task.id]);
  for (const [i, s] of siblings.entries()) await run('UPDATE tasks SET position=? WHERE id=?', [i, s.id]);
  if (task.column_id !== columnId) await renumber(task.column_id);
}

module.exports = { h, HttpError, membership, ownerOf, loadOr404, boardPayload, placeTask };
