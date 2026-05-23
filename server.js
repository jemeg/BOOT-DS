require('dotenv').config();
const http = require('http');
const { initializeBot } = require('./bot');
const db = require('./db');

const PORT = process.env.PORT || 3000;

(async () => {
  await db.connect();
  initializeBot();
})();

http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
  res.end('🤖 البوت يعمل');
}).listen(PORT, () => {
  console.log(`🌐 الخادم على http://localhost:${PORT}`);
});
