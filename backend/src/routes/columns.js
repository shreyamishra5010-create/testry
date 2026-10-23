const router = require('express').Router();
const { run, all } = require('../db');
const { h, membership, loadOr404 } = require('../access');

router.patch('/:id', h(async (req, res) => {
  const c = await loadOr404('columns', req.params.id);
  await membership(c.board_id, req.user.id);
  const name = String(req.body.name || '').trim();
  if (!name) return res.status(400).json({ error: 'Column name is required.' });
  await run('UPDATE columns SET name=? WHERE id=?', [name, c.id]);
  res.json({ ...c, name });
}));

// Policy: deleting a column deletes its tasks (and their comments).
router.delete('/:id', h(async (req, res) => {
  const c = await loadOr404('columns', req.params.id);
  await membership(c.board_id, req.user.id);
  const removed = await run('DELETE FROM tasks WHERE column_id=?', [c.id]);
  await run('DELETE FROM columns WHERE id=?', [c.id]);
  const rest = await all('SELECT id FROM columns WHERE board_id=? ORDER BY position, id', [c.board_id]);
  for (const [i, r] of rest.entries()) await run('UPDATE columns SET position=? WHERE id=?', [i, r.id]);
  res.json({ ok: true, deleted_tasks: removed.changes });
}));

module.exports = router;
