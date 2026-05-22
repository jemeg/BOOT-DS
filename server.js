require('dotenv').config();
const express = require('express');
const path = require('path');
const cors = require('cors');
const db = require('./db');
const { initializeBot } = require('./bot');

const app = express();
const PORT = process.env.PORT || 3000;

app.use(cors());
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

initializeBot();

app.get('/api/applications', (req, res) => {
  const { status } = req.query;
  res.json(db.applications.getAll(status || null));
});

app.get('/api/applications/:id', (req, res) => {
  const app = db.applications.getById(req.params.id);
  if (!app) return res.status(404).json({ error: 'الطلب غير موجود' });
  res.json(app);
});

app.put('/api/applications/:id/approve', (req, res) => {
  const { reviewed_by } = req.body;
  const app = db.applications.getById(req.params.id);
  if (!app) return res.status(404).json({ error: 'الطلب غير موجود' });
  if (app.status !== 'pending') return res.status(400).json({ error: 'تم معالجة هذا الطلب بالفعل' });
  db.applications.update(req.params.id, {
    status: 'approved',
    reviewed_by: reviewed_by || 'Admin',
    reviewed_at: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString()
  });
  db.logs.create({
    application_id: req.params.id, action: 'approve',
    performed_by: reviewed_by || 'Admin',
    details: `تم قبول طلب ${app.full_name}`
  });
  res.json({ message: '✅ تم قبول الطلب' });
});

app.put('/api/applications/:id/reject', (req, res) => {
  const { reviewed_by, rejection_reason } = req.body;
  if (!rejection_reason) return res.status(400).json({ error: 'يجب كتابة سبب الرفض' });
  const app = db.applications.getById(req.params.id);
  if (!app) return res.status(404).json({ error: 'الطلب غير موجود' });
  if (app.status !== 'pending') return res.status(400).json({ error: 'تم معالجة هذا الطلب بالفعل' });
  db.applications.update(req.params.id, {
    status: 'rejected', rejection_reason,
    reviewed_by: reviewed_by || 'Admin',
    reviewed_at: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString()
  });
  db.logs.create({
    application_id: req.params.id, action: 'reject',
    performed_by: reviewed_by || 'Admin',
    details: `تم رفض طلب ${app.full_name} بسبب: ${rejection_reason}`
  });
  res.json({ message: '❌ تم رفض الطلب' });
});

app.delete('/api/applications/:id', (req, res) => {
  const deleted = db.applications.delete(req.params.id);
  if (!deleted) return res.status(404).json({ error: 'الطلب غير موجود' });
  db.logs.create({
    application_id: req.params.id, action: 'delete',
    performed_by: 'Admin',
    details: `تم حذف طلب ${deleted.full_name}`
  });
  res.json({ message: '🗑️ تم حذف الطلب' });
});

app.get('/api/logs', (req, res) => {
  res.json(db.logs.getAll());
});

app.get('/api/stats', (req, res) => {
  res.json(db.applications.getStats());
});

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'public', 'admin.html'));
});

app.listen(PORT, () => {
  console.log(`🌐 لوحة المراقبة على http://localhost:${PORT}`);
});
