require('dotenv').config();
const fs = require('fs');
const path = require('path');
const { MongoClient } = require('mongodb');

const MONGO_URI = process.env.MONGODB_URI;
const DATA_FILE = path.join(__dirname, 'data.json');

let mode = 'file';
let client = null;
let _db = null;

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substring(2, 8);
}

function readData() {
  try {
    if (!fs.existsSync(DATA_FILE)) {
      const initial = { applications: [], logs: [], settings: { submissions_open: true } };
      fs.writeFileSync(DATA_FILE, JSON.stringify(initial, null, 2));
      return initial;
    }
    return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
  } catch {
    return { applications: [], logs: [], settings: { submissions_open: true } };
  }
}

function writeData(data) {
  fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
}

async function connect() {
  if (!MONGO_URI || MONGO_URI.includes('<username>')) {
    console.log('📁 استخدام التخزين المحلي (data.json)');
    return;
  }
  try {
    client = new MongoClient(MONGO_URI);
    await client.connect();
    _db = client.db('health_ministry_bot');
    await _db.collection('settings').updateOne(
      { _id: 'settings' },
      { $setOnInsert: { submissions_open: true } },
      { upsert: true }
    );
    mode = 'mongo';
    console.log('✅ متصل بقاعدة البيانات');
  } catch (err) {
    console.warn('⚠️ فشل الاتصال بقاعدة البيانات، استخدام الملف المحلي:', err.message);
  }
}

const _applications = {
  async getAll(status) {
    if (mode === 'mongo') {
      const filter = {};
      if (status) filter.status = status;
      return _db.collection('applications').find(filter).sort({ created_at: -1 }).toArray();
    }
    let apps = readData().applications;
    if (status) apps = apps.filter(a => a.status === status);
    return apps.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  },
  async getByUser(discordUserId) {
    if (mode === 'mongo') return _db.collection('applications').find({ discord_user_id: discordUserId }).toArray();
    return readData().applications.filter(a => a.discord_user_id === discordUserId);
  },
  async getById(id) {
    if (mode === 'mongo') return _db.collection('applications').findOne({ id });
    return readData().applications.find(a => a.id === id) || null;
  },
  async create(appData) {
    const app = { id: generateId(), ...appData, status: 'pending', created_at: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString() };
    if (mode === 'mongo') {
      await _db.collection('applications').insertOne(app);
    } else {
      const data = readData();
      data.applications.push(app);
      writeData(data);
    }
    return app;
  },
  async update(id, updates) {
    if (mode === 'mongo') {
      await _db.collection('applications').updateOne({ id }, { $set: updates });
      return _db.collection('applications').findOne({ id });
    }
    const data = readData();
    const index = data.applications.findIndex(a => a.id === id);
    if (index === -1) return null;
    data.applications[index] = { ...data.applications[index], ...updates };
    writeData(data);
    return data.applications[index];
  },
  async delete(id) {
    if (mode === 'mongo') {
      const doc = await _db.collection('applications').findOne({ id });
      if (doc) await _db.collection('applications').deleteOne({ id });
      return doc || false;
    }
    const data = readData();
    const index = data.applications.findIndex(a => a.id === id);
    if (index === -1) return false;
    const deleted = data.applications.splice(index, 1)[0];
    writeData(data);
    return deleted;
  },
  async getStats() {
    if (mode === 'mongo') {
      const [total, pending, approved, rejected] = await Promise.all([
        _db.collection('applications').countDocuments(),
        _db.collection('applications').countDocuments({ status: 'pending' }),
        _db.collection('applications').countDocuments({ status: 'approved' }),
        _db.collection('applications').countDocuments({ status: 'rejected' })
      ]);
      return { total, pending, approved, rejected };
    }
    const apps = readData().applications;
    return {
      total: apps.length,
      pending: apps.filter(a => a.status === 'pending').length,
      approved: apps.filter(a => a.status === 'approved').length,
      rejected: apps.filter(a => a.status === 'rejected').length
    };
  }
};

const _settings = {
  async get() {
    if (mode === 'mongo') {
      const doc = await _db.collection('settings').findOne({ _id: 'settings' });
      return doc || { submissions_open: true };
    }
    return readData().settings || { submissions_open: true };
  },
  async update(key, value) {
    if (mode === 'mongo') {
      await _db.collection('settings').updateOne({ _id: 'settings' }, { $set: { [key]: value } });
      return _settings.get();
    }
    const data = readData();
    if (!data.settings) data.settings = { submissions_open: true };
    data.settings[key] = value;
    writeData(data);
    return data.settings;
  }
};

const _logs = {
  async create(entry) {
    const log = { id: generateId(), ...entry, created_at: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString() };
    if (mode === 'mongo') {
      await _db.collection('logs').insertOne(log);
    } else {
      const data = readData();
      data.logs.push(log);
      writeData(data);
    }
    return log;
  },
  async getAll() {
    if (mode === 'mongo') return _db.collection('logs').find().sort({ created_at: -1 }).toArray();
    return readData().logs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
  }
};

function readDataSync() {
  return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
}

const _fast = {
  get settings() {
    try { return readDataSync().settings || { submissions_open: true }; } catch { return { submissions_open: true }; }
  },
  getUserApps(discordUserId) {
    try { return readDataSync().applications.filter(a => a.discord_user_id === discordUserId); } catch { return []; }
  }
};

module.exports = { connect, applications: _applications, settings: _settings, logs: _logs, fast: _fast };
