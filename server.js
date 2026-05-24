require('dotenv').config();
const express = require('express');
const http = require('http');
const { initializeBot, getClient } = require('./bot');
const db = require('./db');

const PORT = process.env.PORT || 3000;
const app = express();

app.get('/', (req, res) => {
  res.send('Bot is running');
});

app.get('/health', (req, res) => {
  const client = getClient();
  res.json({ status: 'ok', bot: client?.isReady() ? 'connected' : 'disconnected' });
});

(async () => {
  await db.connect();
  initializeBot();
})();

const server = app.listen(PORT, () => {
  console.log(`🌐 الخادم على http://localhost:${PORT}`);
});

// Ping دوري للحفاظ على البوت شغال على Render
setInterval(() => {
  http.get(`http://localhost:${PORT}`, (res) => {
    console.log('✅ Ping تم بنجاح');
  }).on('error', (err) => {
    console.error('❌ Ping فشل:', err.message);
  });
}, 5 * 60 * 1000); // كل 5 دقائق

process.on('unhandledRejection', console.error);
process.on('uncaughtException', console.error);
