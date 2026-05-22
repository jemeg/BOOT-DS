const fs = require('fs');
const path = require('path');

const DATA_FILE = path.join(__dirname, 'data.json');

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).substring(2, 8);
}

function readData() {
  try {
    if (!fs.existsSync(DATA_FILE)) {
      const initial = { applications: [], logs: [] };
      fs.writeFileSync(DATA_FILE, JSON.stringify(initial, null, 2));
      return initial;
    }
    return JSON.parse(fs.readFileSync(DATA_FILE, 'utf8'));
  } catch {
    return { applications: [], logs: [] };
  }
}

function writeData(data) {
  fs.writeFileSync(DATA_FILE, JSON.stringify(data, null, 2));
}

const db = {
  applications: {
    getAll(status) {
      const data = readData();
      let apps = data.applications;
      if (status) {
        apps = apps.filter(a => a.status === status);
      }
      return apps.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    },
    getByUser(discordUserId) {
      const data = readData();
      return data.applications.filter(a => a.discord_user_id === discordUserId);
    },
    getById(id) {
      const data = readData();
      return data.applications.find(a => a.id === id) || null;
    },
    create(appData) {
      const data = readData();
      const app = {
        id: generateId(),
        ...appData,
        status: 'pending',
        rejection_reason: null,
        reviewed_by: null,
        reviewed_at: null,
        created_at: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString()
      };
      data.applications.push(app);
      writeData(data);
      return app;
    },
    update(id, updates) {
      const data = readData();
      const index = data.applications.findIndex(a => a.id === id);
      if (index === -1) return null;
      data.applications[index] = { ...data.applications[index], ...updates };
      writeData(data);
      return data.applications[index];
    },
    delete(id) {
      const data = readData();
      const index = data.applications.findIndex(a => a.id === id);
      if (index === -1) return false;
      const deleted = data.applications.splice(index, 1)[0];
      writeData(data);
      return deleted;
    },
    getStats() {
      const data = readData();
      const apps = data.applications;
      return {
        total: apps.length,
        pending: apps.filter(a => a.status === 'pending').length,
        approved: apps.filter(a => a.status === 'approved').length,
        rejected: apps.filter(a => a.status === 'rejected').length
      };
    }
  },
  logs: {
    create(entry) {
      const data = readData();
      const log = {
        id: generateId(),
        ...entry,
        created_at: new Date(Date.now() + 3 * 60 * 60 * 1000).toISOString()
      };
      data.logs.push(log);
      writeData(data);
      return log;
    },
    getAll() {
      const data = readData();
      return data.logs.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    }
  }
};

module.exports = db;
