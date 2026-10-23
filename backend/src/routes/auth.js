const router = require('express').Router();
const bcrypt = require('bcryptjs');
const { run, get, now } = require('../db');
const { sign, requireAuth } = require('../auth');
const { h } = require('../access');

const EMAIL = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

router.post('/register', h(async (req, res) => {
  const name = String(req.body.name || '').trim();
  const email = String(req.body.email || '').trim().toLowerCase();
  const password = String(req.body.password || '');
  if (!name || !EMAIL.test(email) || password.length < 8) {
    return res.status(400).json({ error: 'Name, a valid email, and an 8-character password are required.' });
  }
  if (await get('SELECT id FROM users WHERE email=?', [email])) {
    return res.status(409).json({ error: 'An account with that email already exists.' });
  }
  const r = await run('INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)', [name, email, bcrypt.hashSync(password, 10), now()]);
  const user = { id: r.id, name, email };
  res.status(201).json({ token: sign(user), user });
}));

router.post('/login', h(async (req, res) => {
  const user = await get('SELECT * FROM users WHERE email=?', [String(req.body.email || '').trim().toLowerCase()]);
  if (!user || !bcrypt.compareSync(String(req.body.password || ''), user.password_hash)) {
    return res.status(401).json({ error: 'Email or password is incorrect.' });
  }
  const safe = { id: user.id, name: user.name, email: user.email };
  res.json({ token: sign(safe), user: safe });
}));

const me = [requireAuth, h(async (req, res) => {
  const user = await get('SELECT id,name,email FROM users WHERE id=?', [req.user.id]);
  if (!user) return res.status(401).json({ error: 'Please sign in to continue.' });
  res.json({ user });
})];

module.exports = { router, me };
