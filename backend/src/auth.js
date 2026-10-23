const jwt = require('jsonwebtoken');

const JWT_SECRET = process.env.JWT_SECRET;
if (!JWT_SECRET) throw new Error('JWT_SECRET is required');

const sign = (user) => jwt.sign({ id: user.id, email: user.email, name: user.name }, JWT_SECRET, { expiresIn: '7d' });

function requireAuth(req, res, next) {
  const raw = req.headers.authorization || '';
  try {
    if (!raw.startsWith('Bearer ')) throw new Error('missing');
    req.user = jwt.verify(raw.slice(7), JWT_SECRET);
    next();
  } catch {
    res.status(401).json({ error: 'Please sign in to continue.' });
  }
}

module.exports = { sign, requireAuth };
