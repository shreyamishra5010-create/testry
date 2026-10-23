const router = require('express').Router();
const { run, all } = require('../db');
const { h, membership, loadOr404, logActivity } = require('../access');

const renumberColumns = async (ids) => {
  for (const [i, id] of ids.entries()) await run('UPDATE columns SET position=? WHERE id=?', [i, id]);
};

router.patch('/:id', h(async (req, res) => {
  const c = await loadOr404('columns', req.params.id);
  await membership(c.board_id, req.user.id);
  const name = String(req.body.name || '').trim();
  if (!name) return res.status(400).json({ error: 'Column name is required.' });
  await run('UPDATE columns SET name=? WHERE id=?', [name, c.id]);
  if (name !== c.name) await logActivity(c.board_id, req.user.id, 'column.renamed', `renamed column "${c.name}" to "${name}"`);
  res.json({ ...c, name });
}));

// Moves the column to a 0-based index among the board's columns, then renumbers densely.
router.patch('/:id/move', h(async (req, res) => {
  const c = await loadOr404('columns', req.params.id);
  await membership(c.board_id, req.user.id);
  const raw = req.body.position;
  const index = typeof raw === 'number' || (typeof raw === 'string' && raw.trim() !== '') ? Number(raw) : NaN;
  if (!Number.isInteger(index)) return res.status(400).json({ error: 'Position must be a whole number.' });
  const ids = (await all('SELECT id FROM columns WHERE board_id=? AND id<>? ORDER BY position, id', [c.board_id, c.id])).map((r) => r.id);
  const at = Math.max(0, Math.min(index, ids.length));
  ids.splice(at, 0, c.id);
  await renumberColumns(ids);
  if (at !== c.position) await logActivity(c.board_id, req.user.id, 'column.moved', `moved column "${c.name}" to position ${at + 1}`);
  res.json(await all('SELECT id, name, position FROM columns WHERE board_id=? ORDER BY position', [c.board_id]));
}));

// Policy: deleting a column deletes its tasks (and their comments).
router.delete('/:id', h(async (req, res) => {
  const c = await loadOr404('columns', req.params.id);
  await membership(c.board_id, req.user.id);
  const removed = await run('DELETE FROM tasks WHERE column_id=?', [c.id]);
  await run('DELETE FROM columns WHERE id=?', [c.id]);
  await renumberColumns((await all('SELECT id FROM columns WHERE board_id=? ORDER BY position, id', [c.board_id])).map((r) => r.id));
  const n = removed.changes;
  await logActivity(c.board_id, req.user.id, 'column.deleted', `deleted column "${c.name}"${n ? ` and ${n} task${n > 1 ? 's' : ''}` : ''}`);
  res.json({ ok: true, deleted_tasks: n });
}));

module.exports = router;
