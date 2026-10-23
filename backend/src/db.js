const fs = require('fs');
const path = require('path');
const sqlite3 = require('sqlite3');

const ROOT = path.join(__dirname, '..');
const db = new sqlite3.Database(path.join(ROOT, 'taskboard.sqlite'));

const run = (sql, params = []) => new Promise((resolve, reject) =>
  db.run(sql, params, function (err) { err ? reject(err) : resolve({ id: this.lastID, changes: this.changes }); }));
const get = (sql, params = []) => new Promise((resolve, reject) =>
  db.get(sql, params, (err, row) => (err ? reject(err) : resolve(row))));
const all = (sql, params = []) => new Promise((resolve, reject) =>
  db.all(sql, params, (err, rows) => (err ? reject(err) : resolve(rows))));
const exec = (sql) => new Promise((resolve, reject) => db.exec(sql, (err) => (err ? reject(err) : resolve())));
const now = () => new Date().toISOString();

const ready = (async () => {
  await exec(fs.readFileSync(path.join(ROOT, 'schema.sql'), 'utf8'));
  const { n } = await get('SELECT COUNT(*) n FROM users');
  if (!n) await exec(fs.readFileSync(path.join(ROOT, 'seed.sql'), 'utf8'));
})();

module.exports = { run, get, all, now, ready };
