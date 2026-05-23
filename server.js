require('dotenv').config();
const { initializeBot } = require('./bot');

initializeBot();

console.log('🤖 البوت يعمل بدون لوحة تحكم ويب');
