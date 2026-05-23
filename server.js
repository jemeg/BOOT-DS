require('dotenv').config();
const http = require('http');
const { connect } = require('./db');
const { initializeBot } = require('./bot');

const PORT = process.env.PORT || 3000;

async function start() {
  await connect();

  http.createServer((req, res) => {
    res.writeHead(200, { 'Content-Type': 'text/plain' });
    res.end('Bot is running!');
  }).listen(PORT, () => {
    console.log(`🌐 الخادم على http://localhost:${PORT}`);
  });

  initializeBot();
}

start();
