require('dotenv').config();
const http = require('http');
const { initializeBot, getClient } = require('./bot');
const db = require('./db');

const PORT = process.env.PORT || 3000;

(async () => {
  await db.connect();
  initializeBot();
})();

const server = http.createServer((req, res) => {
  if (req.url === '/health') {
    const client = getClient();
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify({ status: 'ok', bot: client?.isReady() ? 'connected' : 'disconnected' }));
  } else {
    res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
    res.end('🤖 البوت يعمل');
  }
});

server.listen(PORT, () => {
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
