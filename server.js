require('dotenv').config();
const http = require('http');
const { initializeBot } = require('./bot');

const PORT = process.env.PORT || 3000;

initializeBot();

http.createServer((req, res) => {
  res.writeHead(200, { 'Content-Type': 'text/plain; charset=utf-8' });
  res.end('🤖 البوت يعمل');
}).listen(PORT, () => {
  console.log(`🌐 الخادم على http://localhost:${PORT}`);
});
