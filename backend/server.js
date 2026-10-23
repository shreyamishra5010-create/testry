const express = require('express');
const cors = require('cors');
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const sqlite3 = require('sqlite3').verbose();
const path = require('path');
require('dotenv').config({ path: path.join(__dirname, '.env') });

const app = express();
const PORT = 8001;
const JWT_SECRET = process.env.JWT_SECRET;
if (!JWT_SECRET) throw new Error('JWT_SECRET is required');
const db = new sqlite3.Database(path.join(__dirname, 'taskboard.sqlite'));
app.use(cors({ origin: true, credentials: true }));
app.use(express.json());

const run = (sql, params = []) => new Promise((resolve, reject) => db.run(sql, params, function (err) { err ? reject(err) : resolve({ id: this.lastID, changes: this.changes }); }));
const get = (sql, params = []) => new Promise((resolve, reject) => db.get(sql, params, (err, row) => err ? reject(err) : resolve(row)));
const all = (sql, params = []) => new Promise((resolve, reject) => db.all(sql, params, (err, rows) => err ? reject(err) : resolve(rows)));
const now = () => new Date().toISOString();

db.serialize(async () => {
  await run('PRAGMA foreign_keys = ON');
  await run(`CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TEXT NOT NULL)`);
  await run(`CREATE TABLE IF NOT EXISTS boards (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, description TEXT DEFAULT '', owner_id INTEGER NOT NULL, created_at TEXT NOT NULL, FOREIGN KEY(owner_id) REFERENCES users(id) ON DELETE CASCADE)`);
  await run(`CREATE TABLE IF NOT EXISTS board_members (board_id INTEGER NOT NULL, user_id INTEGER NOT NULL, role TEXT DEFAULT 'member', PRIMARY KEY(board_id,user_id), FOREIGN KEY(board_id) REFERENCES boards(id) ON DELETE CASCADE, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)`);
  await run(`CREATE TABLE IF NOT EXISTS columns (id INTEGER PRIMARY KEY AUTOINCREMENT, board_id INTEGER NOT NULL, name TEXT NOT NULL, position INTEGER NOT NULL, color TEXT DEFAULT '#0052CC', FOREIGN KEY(board_id) REFERENCES boards(id) ON DELETE CASCADE)`);
  await run(`CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY AUTOINCREMENT, board_id INTEGER NOT NULL, column_id INTEGER NOT NULL, title TEXT NOT NULL, description TEXT DEFAULT '', priority TEXT DEFAULT 'medium', due_date TEXT, assignee_id INTEGER, position INTEGER NOT NULL, created_by INTEGER NOT NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL, FOREIGN KEY(board_id) REFERENCES boards(id) ON DELETE CASCADE, FOREIGN KEY(column_id) REFERENCES columns(id) ON DELETE CASCADE, FOREIGN KEY(assignee_id) REFERENCES users(id) ON DELETE SET NULL)`);
  await run(`CREATE TABLE IF NOT EXISTS comments (id INTEGER PRIMARY KEY AUTOINCREMENT, task_id INTEGER NOT NULL, user_id INTEGER NOT NULL, body TEXT NOT NULL, created_at TEXT NOT NULL, FOREIGN KEY(task_id) REFERENCES tasks(id) ON DELETE CASCADE, FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE)`);
  const demo = await get('SELECT id FROM users WHERE email=?', ['demo@taskboard.local']);
  if (!demo) {
    const user = await run('INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)', ['Alex Morgan', 'demo@taskboard.local', bcrypt.hashSync('demo1234', 10), now()]);
    const board = await run('INSERT INTO boards(name,description,owner_id,created_at) VALUES(?,?,?,?)', ['Product Launch', 'Coordinate the next release from idea to shipped.', user.id, now()]);
    await run('INSERT INTO board_members(board_id,user_id,role) VALUES(?,?,?)', [board.id, user.id, 'owner']);
    const cols = [];
    for (const [name, color] of [['To Do','#0052CC'],['In Progress','#FFAB00'],['Done','#00875A']]) cols.push((await run('INSERT INTO columns(board_id,name,position,color) VALUES(?,?,?,?)', [board.id,name,cols.length,color])).id);
    const tasks = [['Audit onboarding flow','Review activation drop-offs and list the top three fixes.','high',cols[0],'2026-05-22'],['Design release notes','Draft the customer-facing release story with screenshots.','medium',cols[1],null],['QA regression pass','Run the smoke test across the new workspace experience.','low',cols[2],null]];
    for (const [title,description,priority,column,due_date] of tasks) await run('INSERT INTO tasks(board_id,column_id,title,description,priority,due_date,position,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)', [board.id,column,title,description,priority,due_date,tasks.indexOf(tasks.find(t=>t[0]===title)),user.id,now(),now()]);
  }
});

function token(user) { return jwt.sign({ id: user.id, email: user.email, name: user.name }, JWT_SECRET, { expiresIn: '7d' }); }
function auth(req, res, next) { const raw = req.headers.authorization || ''; try { if (!raw.startsWith('Bearer ')) throw new Error(); req.user = jwt.verify(raw.slice(7), JWT_SECRET); next(); } catch { res.status(401).json({ error: 'Please sign in to continue.' }); } }
async function member(boardId, userId) { return get('SELECT b.*, bm.role FROM boards b JOIN board_members bm ON bm.board_id=b.id WHERE b.id=? AND bm.user_id=?', [boardId,userId]); }
async function boardPayload(boardId) {
  const board = await get('SELECT b.*, u.name owner_name FROM boards b JOIN users u ON u.id=b.owner_id WHERE b.id=?', [boardId]);
  if (!board) return null;
  board.columns = await all('SELECT * FROM columns WHERE board_id=? ORDER BY position', [boardId]);
  for (const col of board.columns) col.tasks = await all(`SELECT t.*, u.name assignee_name, substr(u.name,1,1) assignee_initial FROM tasks t LEFT JOIN users u ON u.id=t.assignee_id WHERE t.column_id=? ORDER BY t.position`, [col.id]);
  board.members = await all('SELECT u.id,u.name,u.email,bm.role FROM board_members bm JOIN users u ON u.id=bm.user_id WHERE bm.board_id=?', [boardId]);
  return board;
}

app.get('/api/health', (_, res) => res.json({ ok: true, service: 'task-board-api' }));
app.post('/api/auth/register', async (req,res) => { try { const {name,email,password}=req.body; if (!name || !email || !password || password.length < 8) return res.status(400).json({error:'Name, email, and an 8-character password are required.'}); const result=await run('INSERT INTO users(name,email,password_hash,created_at) VALUES(?,?,?,?)',[name,email.toLowerCase(),bcrypt.hashSync(password,10),now()]); const user={id:result.id,name,email:email.toLowerCase()}; res.status(201).json({token:token(user),user}); } catch { res.status(409).json({error:'An account with that email already exists.'}); } });
app.post('/api/auth/login', async (req,res) => { const user=await get('SELECT * FROM users WHERE email=?',[String(req.body.email||'').toLowerCase()]); if (!user || !bcrypt.compareSync(req.body.password||'',user.password_hash)) return res.status(401).json({error:'Email or password is incorrect.'}); const safe={id:user.id,name:user.name,email:user.email}; res.json({token:token(safe),user:safe}); });
app.get('/api/me', auth, async (req,res) => res.json({user: await get('SELECT id,name,email FROM users WHERE id=?',[req.user.id])}));
app.get('/api/boards', auth, async (req,res) => res.json(await all(`SELECT b.*, u.name owner_name, (SELECT COUNT(*) FROM tasks t WHERE t.board_id=b.id) task_count FROM boards b JOIN board_members bm ON bm.board_id=b.id JOIN users u ON u.id=b.owner_id WHERE bm.user_id=? ORDER BY b.created_at DESC`,[req.user.id])));
app.post('/api/boards', auth, async (req,res) => { const name=String(req.body.name||'').trim(); if(!name)return res.status(400).json({error:'Board name is required.'}); const b=await run('INSERT INTO boards(name,description,owner_id,created_at) VALUES(?,?,?,?)',[name,req.body.description||'',req.user.id,now()]); await run('INSERT INTO board_members(board_id,user_id,role) VALUES(?,?,?)',[b.id,req.user.id,'owner']); for(const [n,c] of [['To Do','#0052CC'],['In Progress','#FFAB00'],['Done','#00875A']]) await run('INSERT INTO columns(board_id,name,position,color) VALUES(?,?,?,?)',[b.id,n,['To Do','In Progress','Done'].indexOf(n),c]); res.status(201).json(await boardPayload(b.id)); });
app.patch('/api/boards/:id', auth, async (req,res) => { const b=await member(req.params.id,req.user.id); if(!b || b.owner_id!==req.user.id)return res.status(403).json({error:'Only the board owner can rename it.'}); await run('UPDATE boards SET name=?,description=? WHERE id=?',[req.body.name,b.description,req.params.id]); res.json(await boardPayload(req.params.id)); });
app.delete('/api/boards/:id', auth, async (req,res) => { const b=await member(req.params.id,req.user.id); if(!b || b.owner_id!==req.user.id)return res.status(403).json({error:'Only the board owner can delete it.'}); await run('DELETE FROM boards WHERE id=?',[req.params.id]); res.json({ok:true}); });
app.get('/api/boards/:id', auth, async (req,res) => { if(!await member(req.params.id,req.user.id))return res.status(403).json({error:'You do not have access to this board.'}); res.json(await boardPayload(req.params.id)); });
app.post('/api/boards/:id/columns', auth, async(req,res)=>{if(!await member(req.params.id,req.user.id))return res.status(403).json({error:'Access denied.'}); const max=await get('SELECT COALESCE(MAX(position),-1) p FROM columns WHERE board_id=?',[req.params.id]); const c=await run('INSERT INTO columns(board_id,name,position,color) VALUES(?,?,?,?)',[req.params.id,req.body.name||'New column',max.p+1,req.body.color||'#6554C0']); res.status(201).json({id:c.id});});
app.patch('/api/columns/:id', auth, async(req,res)=>{const c=await get('SELECT * FROM columns WHERE id=?',[req.params.id]);if(!c||!await member(c.board_id,req.user.id))return res.status(403).json({error:'Access denied.'});await run('UPDATE columns SET name=? WHERE id=?',[req.body.name,c.id]);res.json({ok:true});});
app.delete('/api/columns/:id', auth, async(req,res)=>{const c=await get('SELECT * FROM columns WHERE id=?',[req.params.id]);if(!c||!await member(c.board_id,req.user.id))return res.status(403).json({error:'Access denied.'});const target=await get('SELECT id FROM columns WHERE board_id=? AND name=?',[c.board_id,'To Do']);if(req.body.policy==='move'&&target)await run('UPDATE tasks SET column_id=? WHERE column_id=?',[target.id,c.id]);await run('DELETE FROM columns WHERE id=?',[c.id]);res.json({ok:true});});
app.post('/api/boards/:id/tasks', auth, async(req,res)=>{if(!await member(req.params.id,req.user.id))return res.status(403).json({error:'Access denied.'});const max=await get('SELECT COALESCE(MAX(position),-1) p FROM tasks WHERE column_id=?',[req.body.column_id]);const r=await run('INSERT INTO tasks(board_id,column_id,title,description,priority,due_date,assignee_id,position,created_by,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?,?)',[req.params.id,req.body.column_id,req.body.title,req.body.description||'',req.body.priority||'medium',req.body.due_date||null,req.body.assignee_id||null,max.p+1,req.user.id,now(),now()]);res.status(201).json({id:r.id});});
app.patch('/api/tasks/:id', auth, async(req,res)=>{const t=await get('SELECT * FROM tasks WHERE id=?',[req.params.id]);if(!t||!await member(t.board_id,req.user.id))return res.status(403).json({error:'Access denied.'});const fields=['title','description','priority','due_date','assignee_id','column_id'];const data=fields.map(k=>req.body[k]===undefined?t[k]:req.body[k]);if(req.body.column_id&&req.body.column_id!==t.column_id){const max=await get('SELECT COALESCE(MAX(position),-1) p FROM tasks WHERE column_id=?',[req.body.column_id]);data[fields.indexOf('position')]=max.p+1;}await run('UPDATE tasks SET title=?,description=?,priority=?,due_date=?,assignee_id=?,column_id=?,updated_at=? WHERE id=?',[...data,now(),t.id]);res.json({ok:true});});
app.delete('/api/tasks/:id', auth, async(req,res)=>{const t=await get('SELECT * FROM tasks WHERE id=?',[req.params.id]);if(!t||!await member(t.board_id,req.user.id))return res.status(403).json({error:'Access denied.'});await run('DELETE FROM tasks WHERE id=?',[t.id]);res.json({ok:true});});
app.patch('/api/tasks/:id/move', auth, async(req,res)=>{const t=await get('SELECT * FROM tasks WHERE id=?',[req.params.id]);if(!t||!await member(t.board_id,req.user.id))return res.status(403).json({error:'Access denied.'});await run('UPDATE tasks SET column_id=?,position=?,updated_at=? WHERE id=?',[req.body.column_id,req.body.position||0,now(),t.id]);res.json({ok:true});});
app.get('/api/tasks/:id/comments',auth,async(req,res)=>res.json(await all('SELECT c.*,u.name author_name,substr(u.name,1,1) author_initial FROM comments c JOIN users u ON u.id=c.user_id WHERE c.task_id=? ORDER BY c.created_at',[req.params.id])));
app.post('/api/tasks/:id/comments',auth,async(req,res)=>{const t=await get('SELECT * FROM tasks WHERE id=?',[req.params.id]);if(!t||!await member(t.board_id,req.user.id))return res.status(403).json({error:'Access denied.'});const r=await run('INSERT INTO comments(task_id,user_id,body,created_at) VALUES(?,?,?,?)',[t.id,req.user.id,req.body.body,now()]);res.status(201).json({id:r.id});});
app.delete('/api/comments/:id',auth,async(req,res)=>{await run('DELETE FROM comments WHERE id=? AND user_id=?',[req.params.id,req.user.id]);res.json({ok:true});});
app.post('/api/boards/:id/members',auth,async(req,res)=>{const b=await member(req.params.id,req.user.id);if(!b||b.owner_id!==req.user.id)return res.status(403).json({error:'Only the owner can manage members.'});const u=await get('SELECT id FROM users WHERE email=?',[String(req.body.email||'').toLowerCase()]);if(!u)return res.status(404).json({error:'No registered user found with that email.'});await run('INSERT OR IGNORE INTO board_members(board_id,user_id,role) VALUES(?,?,?)',[b.id,u.id,'member']);res.json(await boardPayload(b.id));});
app.delete('/api/boards/:id/members/:userId',auth,async(req,res)=>{const b=await member(req.params.id,req.user.id);if(!b||b.owner_id!==req.user.id)return res.status(403).json({error:'Only the owner can manage members.'});await run('DELETE FROM board_members WHERE board_id=? AND user_id=?',[b.id,req.params.userId]);res.json({ok:true});});
app.use((err,req,res,next)=>{console.error(err);res.status(500).json({error:'Something went wrong.'});});
app.listen(PORT,'0.0.0.0',()=>console.log(`Task Board API listening on ${PORT}`));