const router = require('express').Router();
const { run, get, all, now } = require('../db');
const { h, membership, ownerOf, boardPayload } = require('../access');

const DEFAULT_COLUMNS = [['To Do', '#0052CC'], ['In Progress', '#FFAB00'], ['Done', '#00875A']];

router.get('/', h(async (req, res) => {
  res.json(await all(`SELECT b.*, u.name owner_name, bm.role,
      (SELECT COUNT(*) FROM tasks t WHERE t.board_id=b.id) task_count,
      (SELECT COUNT(*) FROM tasks t WHERE t.board_id=b.id AND t.due_date IS NOT NULL AND date(t.due_date) BETWEEN date('now') AND date('now','+7 day')) due_soon,
      (SELECT COUNT(*) FROM board_members m WHERE m.board_id=b.id) member_count
    FROM boards b JOIN board_members bm ON bm.board_id=b.id JOIN users u ON u.id=b.owner_id
    WHERE bm.user_id=? ORDER BY b.created_at DESC`, [req.user.id]));
}));

router.post('/', h(async (req, res) => {
  const name = String(req.body.name || '').trim();
  if (!name) return res.status(400).json({ error: 'Board name is required.' });
  const b = await run('INSERT INTO boards(name,description,owner_id,created_at) VALUES(?,?,?,?)', [name, String(req.body.description || ''), req.user.id, now()]);
  await run('INSERT INTO board_members(board_id,user_id,role) VALUES(?,?,?)', [b.id, req.user.id, 'owner']);
  for (const [i, [n, c]] of DEFAULT_COLUMNS.entries()) await run('INSERT INTO columns(board_id,name,position,color) VALUES(?,?,?,?)', [b.id, n, i, c]);
  res.status(201).json(await boardPayload(b.id));
}));

router.get('/:id', h(async (req, res) => {
  await membership(req.params.id, req.user.id);
  res.json(await boardPayload(req.params.id));
}));

router.patch('/:id', h(async (req, res) => {
  const b = await ownerOf(req.params.id, req.user.id, 'edit it');
  const name = req.body.name === undefined ? b.name : String(req.body.name).trim();
  if (!name) return res.status(400).json({ error: 'Board name is required.' });
  const description = req.body.description === undefined ? b.description : String(req.body.description);
  await run('UPDATE boards SET name=?,description=? WHERE id=?', [name, description, b.id]);
  res.json(await boardPayload(b.id));
}));

router.delete('/:id', h(async (req, res) => {
  const b = await ownerOf(req.params.id, req.user.id, 'delete it');
  await run('DELETE FROM boards WHERE id=?', [b.id]);
  res.json({ ok: true });
}));

router.post('/:id/members', h(async (req, res) => {
  const b = await ownerOf(req.params.id, req.user.id, 'manage members');
  const u = await get('SELECT id FROM users WHERE email=?', [String(req.body.email || '').trim().toLowerCase()]);
  if (!u) return res.status(404).json({ error: 'No registered user found with that email.' });
  await run('INSERT OR IGNORE INTO board_members(board_id,user_id,role) VALUES(?,?,?)', [b.id, u.id, 'member']);
  res.json(await boardPayload(b.id));
}));

router.delete('/:id/members/:userId', h(async (req, res) => {
  const b = await ownerOf(req.params.id, req.user.id, 'manage members');
  const userId = Number(req.params.userId);
  if (userId === b.owner_id) return res.status(400).json({ error: 'The board owner cannot be removed.' });
  await run('UPDATE tasks SET assignee_id=NULL WHERE board_id=? AND assignee_id=?', [b.id, userId]);
  await run('DELETE FROM board_members WHERE board_id=? AND user_id=?', [b.id, userId]);
  res.json(await boardPayload(b.id));
}));

router.post('/:id/columns', h(async (req, res) => {
  await membership(req.params.id, req.user.id);
  const name = String(req.body.name || '').trim();
  if (!name) return res.status(400).json({ error: 'Column name is required.' });
  const { p } = await get('SELECT COALESCE(MAX(position),-1) p FROM columns WHERE board_id=?', [req.params.id]);
  const c = await run('INSERT INTO columns(board_id,name,position,color) VALUES(?,?,?,?)', [req.params.id, name, p + 1, req.body.color || '#6554C0']);
  res.status(201).json(await get('SELECT * FROM columns WHERE id=?', [c.id]));
}));

module.exports = router;
