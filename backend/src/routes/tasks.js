const router = require('express').Router();
const { run, get, all, now } = require('../db');
const { h, HttpError, membership, loadOr404, placeTask } = require('../access');

const PRIORITIES = ['low', 'medium', 'high'];

async function columnOnBoard(columnId, boardId) {
  const col = await get('SELECT * FROM columns WHERE id=? AND board_id=?', [columnId, boardId]);
  if (!col) throw new HttpError(400, 'That column does not belong to this board.');
  return col;
}

async function validAssignee(assigneeId, boardId) {
  if (assigneeId === null || assigneeId === '' || assigneeId === undefined) return null;
  const m = await get('SELECT user_id FROM board_members WHERE board_id=? AND user_id=?', [boardId, assigneeId]);
  if (!m) throw new HttpError(400, 'The assignee must be a member of this board.');
  return Number(assigneeId);
}

function validFields(body) {
  if (body.title !== undefined && !String(body.title).trim()) throw new HttpError(400, 'Task title is required.');
  if (body.priority !== undefined && !PRIORITIES.includes(body.priority)) throw new HttpError(400, 'Priority must be low, medium, or high.');
}

const taskRow = (id) => get('SELECT t.*, u.name assignee_name FROM tasks t LEFT JOIN users u ON u.id=t.assignee_id WHERE t.id=?', [id]);

async function createTask(req, res) {
  await membership(req.params.id, req.user.id);
  const b = req.body;
  if (!String(b.title || '').trim()) throw new HttpError(400, 'Task title is required.');
  validFields(b);
  const col = await columnOnBoard(b.column_id, req.params.id);
  const assignee = await validAssignee(b.assignee_id, col.board_id);
  const { p } = await get('SELECT COALESCE(MAX(position),-1) p FROM tasks WHERE column_id=?', [col.id]);
  const r = await run(`INSERT INTO tasks(board_id,column_id,title,description,priority,due_date,assignee_id,position,created_by,created_at,updated_at)
    VALUES(?,?,?,?,?,?,?,?,?,?,?)`, [col.board_id, col.id, String(b.title).trim(), b.description || '', b.priority || 'medium', b.due_date || null, assignee, p + 1, req.user.id, now(), now()]);
  res.status(201).json(await taskRow(r.id));
}

router.patch('/:id', h(async (req, res) => {
  const t = await loadOr404('tasks', req.params.id);
  await membership(t.board_id, req.user.id);
  const b = req.body;
  validFields(b);
  const pick = (k) => (b[k] === undefined ? t[k] : b[k]);
  const assignee = b.assignee_id === undefined ? t.assignee_id : await validAssignee(b.assignee_id, t.board_id);
  await run('UPDATE tasks SET title=?,description=?,priority=?,due_date=?,assignee_id=?,updated_at=? WHERE id=?',
    [String(pick('title')).trim(), pick('description') || '', pick('priority'), pick('due_date') || null, assignee, now(), t.id]);
  if (b.column_id !== undefined && Number(b.column_id) !== t.column_id) {
    const col = await columnOnBoard(b.column_id, t.board_id);
    await placeTask(t, col.id);
  }
  res.json(await taskRow(t.id));
}));

router.patch('/:id/move', h(async (req, res) => {
  const t = await loadOr404('tasks', req.params.id);
  await membership(t.board_id, req.user.id);
  const col = await columnOnBoard(req.body.column_id, t.board_id);
  const index = req.body.position === undefined ? undefined : Number(req.body.position);
  await placeTask(t, col.id, Number.isInteger(index) ? index : undefined);
  res.json(await all('SELECT id, column_id, position FROM tasks WHERE column_id IN (?,?) ORDER BY column_id, position', [t.column_id, col.id]));
}));

router.delete('/:id', h(async (req, res) => {
  const t = await loadOr404('tasks', req.params.id);
  await membership(t.board_id, req.user.id);
  await run('DELETE FROM tasks WHERE id=?', [t.id]);
  res.json({ ok: true });
}));

router.get('/:id/comments', h(async (req, res) => {
  const t = await loadOr404('tasks', req.params.id);
  await membership(t.board_id, req.user.id);
  res.json(await all('SELECT c.*, u.name author_name FROM comments c JOIN users u ON u.id=c.user_id WHERE c.task_id=? ORDER BY c.created_at, c.id', [t.id]));
}));

router.post('/:id/comments', h(async (req, res) => {
  const t = await loadOr404('tasks', req.params.id);
  await membership(t.board_id, req.user.id);
  const body = String(req.body.body || '').trim();
  if (!body) return res.status(400).json({ error: 'Comment cannot be empty.' });
  const r = await run('INSERT INTO comments(task_id,user_id,body,created_at) VALUES(?,?,?,?)', [t.id, req.user.id, body, now()]);
  res.status(201).json(await get('SELECT c.*, u.name author_name FROM comments c JOIN users u ON u.id=c.user_id WHERE c.id=?', [r.id]));
}));

module.exports = { router, createTask: h(createTask) };
