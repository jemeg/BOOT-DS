const { MongoClient } = require('mongodb');

const MONGO_URI = process.env.MONGODB_URI;
const DB_NAME = 'health_ministry_bot';

let client = null;
let _db = null;

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substring(2, 8);
}

async function connect() {
  if (!MONGO_URI) {
    console.warn('⚠️ MONGODB_URI غير معرف');
    return;
  }
  client = new MongoClient(MONGO_URI);
  await client.connect();
  _db = client.db(DB_NAME);
  await _db.collection('settings').updateOne(
    { _id: 'settings' },
    { $setOnInsert: { submissions_open: true } },
    { upsert: true }
  );
  console.log('✅ متصل بقاعدة البيانات');
}

function db() {
  if (!_db) throw new Error('❌ قاعدة البيانات غير متصلة');
  return _db;
}

const _applications = {
  async getAll(status) {
    const filter = {};
    if (status) filter.status = status;
    return db().collection('applications').find(filter).sort({ created_at: -1 }).toArray();
  },
  async getByUser(discordUserId) {
    return db().collection('applications').find({ discord_user_id: discordUserId }).toArray();
  },
  async getById(id) {
    return db().collection('applications').findOne({ id });
  },
  async create(appData) {
    const app = { id: generateId(), ...appData, status: 'pending', created_at: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString() };
    await db().collection('applications').insertOne(app);
    return app;
  },
  async update(id, updates) {
    await db().collection('applications').updateOne({ id }, { $set: updates });
    return db().collection('applications').findOne({ id });
  },
  async delete(id) {
    const doc = await db().collection('applications').findOne({ id });
    if (doc) await db().collection('applications').deleteOne({ id });
    return doc || false;
  },
  async getStats() {
    const [total, pending, approved, rejected] = await Promise.all([
      db().collection('applications').countDocuments(),
      db().collection('applications').countDocuments({ status: 'pending' }),
      db().collection('applications').countDocuments({ status: 'approved' }),
      db().collection('applications').countDocuments({ status: 'rejected' })
    ]);
    return { total, pending, approved, rejected };
  }
};

const _settings = {
  async get() {
    const doc = await db().collection('settings').findOne({ _id: 'settings' });
    return doc || { submissions_open: true };
  },
  async update(key, value) {
    await db().collection('settings').updateOne({ _id: 'settings' }, { $set: { [key]: value } });
    return _settings.get();
  }
};

const _logs = {
  async create(entry) {
    const log = { id: generateId(), ...entry, created_at: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString() };
    await db().collection('logs').insertOne(log);
    return log;
  },
  async getAll() {
    return db().collection('logs').find().sort({ created_at: -1 }).toArray();
  }
};

module.exports = { connect, applications: _applications, settings: _settings, logs: _logs };
