const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });
const express = require('express');
const cors = require('cors');
const { ready } = require('./src/db');
const { requireAuth } = require('./src/auth');
const tasks = require('./src/routes/tasks');
const authRoutes = require('./src/routes/auth');

const PORT = process.env.API_PORT;
if (!PORT) throw new Error('API_PORT is required');

const app = express();
app.use(cors({ origin: true, credentials: true }));
app.use(express.json());

app.get('/api/health', (_, res) => res.json({ ok: true, service: 'task-board-api' }));
app.use('/api/auth', authRoutes.router);
app.get('/api/me', ...authRoutes.me);
app.use('/api/boards', requireAuth, require('./src/routes/boards'));
app.post('/api/boards/:id/tasks', requireAuth, tasks.createTask);
app.use('/api/columns', requireAuth, require('./src/routes/columns'));
app.use('/api/tasks', requireAuth, tasks.router);
app.use('/api/comments', requireAuth, require('./src/routes/comments'));
app.use('/api', (_, res) => res.status(404).json({ error: 'Not found.' }));

app.use((err, req, res, next) => {
  if (err.status) return res.status(err.status).json({ error: err.message });
  console.error(err);
  res.status(500).json({ error: 'Something went wrong.' });
});

ready.then(() => app.listen(PORT, '127.0.0.1', () => console.log(`Task Board API listening on ${PORT}`)));
