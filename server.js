require('dotenv').config();
require('dotenv').config();
const http = require('http');
const { initializeBot } = require('./bot');
const db = require('./db');

const PORT = Number(process.env.PORT || 3000);

async function start() {
  try {
    await db.connect();
    initializeBot();
  } catch (err) {
    console.error('❌ فشل بدء البوت:', err.message || err);
    process.exit(1);
  }
}

process.on('unhandledRejection', (reason) => {
  console.error('❌ وعود غير معالجة:', reason instanceof Error ? reason.message : reason);
});

process.on('uncaughtException', (err) => {
  console.error('❌ خطأ غير معالج:', err.message || err);
  process.exit(1);
});

start();

http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
  res.end('🤖 البوت يعمل بشكل ممتاز');
}).listen(PORT, () => {
  console.log(`🌐 الخادم على http://localhost:${PORT}`);
});
