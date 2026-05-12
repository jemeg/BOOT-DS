import websocket
import json
import threading
import time
import logging
from rules_bot import discord_bot, rules_manager

logger = logging.getLogger(__name__)

class RulesWebSocket:
    def __init__(self):
        self.ws = None
        self.running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.heartbeat_interval = 0
        self.last_heartbeat = 0
        self.sequence = 0
        self.session_id = None
        
    def connect(self):
        """الاتصال بـ Discord WebSocket Gateway"""
        try:
            gateway_url = self.get_gateway_url()
            if not gateway_url:
                logger.error("❌ فشل في الحصول على رابط Gateway")
                return False
            
            self.ws = websocket.WebSocketApp(
                gateway_url,
                on_open=self.on_open,
                on_message=self.on_message,
                on_error=self.on_error,
                on_close=self.on_close
            )
            
            self.running = True
            self.reconnect_attempts = 0
            
            # بدء WebSocket في خيط منفصل
            ws_thread = threading.Thread(target=self.ws.run_forever, kwargs={'ping_interval': 20})
            ws_thread.daemon = True
            ws_thread.start()
            
            logger.info("✅ تم الاتصال بـ WebSocket Gateway")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في الاتصال بـ WebSocket: {e}")
            return False
    
    def get_gateway_url(self):
        """الحصول على رابط WebSocket Gateway"""
        try:
            # استخدام رابط Gateway الافتراضي
            return "wss://gateway.discord.gg/?v=10&encoding=json"
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على رابط Gateway: {e}")
            return None
    
    def on_open(self, ws):
        """عند فتح الاتصال"""
        logger.info("🔗 تم فتح اتصال WebSocket")
        self.send_identify()
    
    def on_message(self, ws, message):
        """استقبال الرسائل من WebSocket"""
        try:
            data = json.loads(message)
            op = data.get('op')
            t = data.get('t')
            d = data.get('d')
            
            # تحديث الـ sequence
            if 's' in data and data['s']:
                self.sequence = data['s']
            
            if op == 10:  # Hello
                self.heartbeat_interval = d.get('heartbeat_interval', 41250)
                self.start_heartbeat()
                logger.info(f"❤️ تم استلام Heartbeat interval: {self.heartbeat_interval}ms")
                
            elif op == 11:  # Heartbeat ACK
                self.last_heartbeat = time.time()
                logger.debug("💓 تم استلام Heartbeat ACK")
                
            elif t == 'READY':
                self.session_id = d.get('session_id')
                user = d.get('user', {})
                logger.info(f"✅ البوت جاهز! {user.get('username')}#{user.get('discriminator')}")
                
            elif t == 'VOICE_STATE_UPDATE':
                self.handle_voice_state_update(d)
                
            elif t == 'GUILD_CREATE':
                logger.info(f"🏰 تم الانضمام للسيرفر: {d.get('name')}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة رسالة WebSocket: {e}")
    
    def on_error(self, ws, error):
        """عند حدوث خطأ"""
        logger.error(f"❌ خطأ في WebSocket: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """عند إغلاق الاتصال"""
        logger.warning(f"⚠️ تم إغلاق اتصال WebSocket: {close_status_code} - {close_msg}")
        self.running = False
        
        # محاولة إعادة الاتصال
        if self.reconnect_attempts < self.max_reconnect_attempts:
            self.reconnect_attempts += 1
            logger.info(f"🔄 محاولة إعادة الاتصال ({self.reconnect_attempts}/{self.max_reconnect_attempts})")
            time.sleep(5)
            self.connect()
    
    def send_identify(self):
        """إرسال رسالة Identify"""
        identify_payload = {
            "op": 2,
            "d": {
                "token": discord_bot.token,
                "intents": 513,  # GUILDS (1) + GUILD_VOICE_STATES (512)
                "properties": {
                    "os": "linux",
                    "browser": "rules_bot",
                    "device": "rules_bot"
                }
            }
        }
        
        if self.session_id:
            # Resume إذا كان لدينا session_id
            identify_payload = {
                "op": 6,
                "d": {
                    "token": discord_bot.token,
                    "session_id": self.session_id,
                    "seq": self.sequence
                }
            }
        
        self.send_json(identify_payload)
    
    def send_json(self, data):
        """إرسال بيانات JSON"""
        if self.ws and self.running:
            try:
                self.ws.send(json.dumps(data))
            except Exception as e:
                logger.error(f"❌ خطأ في إرسال البيانات: {e}")
    
    def start_heartbeat(self):
        """بدء إرسال Heartbeat"""
        def heartbeat_loop():
            while self.running:
                try:
                    heartbeat_payload = {"op": 1, "d": self.sequence}
                    self.send_json(heartbeat_payload)
                    time.sleep(self.heartbeat_interval / 1000)
                except Exception as e:
                    logger.error(f"❌ خطأ في إرسال Heartbeat: {e}")
                    break
        
        heartbeat_thread = threading.Thread(target=heartbeat_loop)
        heartbeat_thread.daemon = True
        heartbeat_thread.start()
    
    def handle_voice_state_update(self, data):
        """معالجة تحديثات حالة الصوت"""
        try:
            member = data.get('member', {})
            user = member.get('user', {})
            user_id = user.get('id')
            username = user.get('username')
            channel_id = data.get('channel_id')
            guild_id = data.get('guild_id')
            
            if not user_id or not guild_id:
                return
            
            # التحقق مما إذا كانت هذه قناة مفعلة للقوانين
            for channel_info in rules_manager.channels:
                if channel_info['id'] == channel_id:
                    self.handle_rules_channel(user_id, username, channel_id, channel_info)
                    break
                    
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة تحديث الصوت: {e}")
    
    def handle_rules_channel(self, user_id, username, channel_id, channel_info):
        """معالجة القناة المفعلة للقوانين"""
        try:
            # مفتاح لتتبع رسائل المستخدم
            user_key = f"{user_id}_{channel_id}"
            
            # إرسال رسالة القوانين عند دخول القناة
            if channel_id not in discord_bot.user_rules_messages:
                discord_bot.user_rules_messages[channel_id] = {}
            
            # إرسال رسالة القوانين
            success, result = discord_bot.send_rules_message(channel_id, username)
            if success:
                message_id = result.get('id')
                discord_bot.user_rules_messages[channel_id][user_id] = message_id
                logger.info(f"📜 تم إرسال قوانين للمستخدم {username} في القناة {channel_info['channel_name']}")
            else:
                logger.error(f"❌ فشل في إرسال القوانين: {result}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة قناة القوانين: {e}")
    
    def cleanup_user_messages(self, user_id, channel_id):
        """حذف رسائل القوانين عند خروج المستخدم"""
        try:
            if channel_id in discord_bot.user_rules_messages:
                if user_id in discord_bot.user_rules_messages[channel_id]:
                    message_id = discord_bot.user_rules_messages[channel_id][user_id]
                    
                    # حذف الرسالة
                    if discord_bot.delete_message(channel_id, message_id):
                        del discord_bot.user_rules_messages[channel_id][user_id]
                        logger.info(f"🗑️ تم حذف رسالة القوانين للمستخدم {user_id}")
                    else:
                        logger.error(f"❌ فشل في حذف رسالة القوانين")
                        
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف رسائل المستخدم: {e}")

# إنشاء كائن WebSocket
rules_websocket = RulesWebSocket()

def start_rules_websocket():
    """بدء WebSocket للقوانين"""
    if rules_websocket.connect():
        logger.info("✅ WebSocket للقوانين بدأ العمل")
        return True
    else:
        logger.error("❌ فشل في بدء WebSocket للقوانين")
        return False
