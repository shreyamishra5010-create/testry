const router = require('express').Router();
const { run } = require('../db');
const { h, loadOr404 } = require('../access');

router.delete('/:id', h(async (req, res) => {
  const c = await loadOr404('comments', req.params.id);
  if (c.user_id !== req.user.id) return res.status(403).json({ error: 'You can only delete your own comments.' });
  await run('DELETE FROM comments WHERE id=?', [c.id]);
  res.json({ ok: true });
}));

module.exports = router;
