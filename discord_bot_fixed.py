import requests
import json
import os
import time
import threading
from flask import Flask, jsonify
import websocket
import logging

# إعداد الـ logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# إعدادات البوت
BOT_TOKEN = os.getenv('DISCORD_TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')
GUILD_ID = os.getenv('GUILD_ID')

# قائمة القوانين
RULES = [
    "📜 **القانون الأول**: احترام جميع الأعضاء",
    "📜 **القانون الثاني**: ممنوع إرسال روابط غير لائقة", 
    "📜 **القانون الثالث**: لا تكرار الرسائل",
    "📜 **القانون الرابع**: استخدام اللغة اللائقة فقط",
    "📜 **القانون الخامس**: عدم نشر معلومات شخصية"
]

# إعدادات Flask
app = Flask('')

@app.route('/')
def home():
    return "بوت ديسكورد يعمل!"

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": time.time()})

@app.route('/test')
def test():
    return jsonify({
        "token_exists": bool(BOT_TOKEN),
        "app_id_exists": bool(APPLICATION_ID),
        "guild_id_exists": bool(GUILD_ID),
        "token_length": len(BOT_TOKEN) if BOT_TOKEN else 0
    })

class DiscordBot:
    def __init__(self):
        self.token = BOT_TOKEN
        self.application_id = APPLICATION_ID
        self.guild_id = GUILD_ID
        self.base_url = "https://discord.com/api/v10"
        self.headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (https://railway.app, 1.0)"
        }
        self.last_voice_state = {}
        self.running = True
        self.ws = None
        self.heartbeat_interval = None
        self.sequence = None
        self.session_id = None
        
    def test_connection(self):
        """اختبار الاتصال بـ Discord API"""
        url = f"{self.base_url}/users/@me"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                bot_info = response.json()
                logger.info(f"✅ الاتصال بنجاح! البوت: {bot_info.get('username')}#{bot_info.get('discriminator')}")
                return True, bot_info
            else:
                logger.error(f"❌ خطأ في الاتصال: {response.status_code} - {response.text}")
                return False, None
        except Exception as e:
            logger.error(f"❌ استثناء في الاتصال: {e}")
            return False, None
    
    def send_message(self, channel_id, content, embed=None):
        """إرسال رسالة إلى قناة"""
        url = f"{self.base_url}/channels/{channel_id}/messages"
        data = {"content": content}
        
        if embed:
            data["embeds"] = [embed]
            
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            if response.status_code == 200:
                logger.info(f"✅ تم إرسال الرسالة بنجاح")
                return True
            else:
                logger.error(f"❌ خطأ في إرسال الرسالة: {response.status_code}")
                logger.error(f"الرد: {response.text}")
                return False
        except Exception as e:
            logger.error(f"❌ استثناء في إرسال الرسالة: {e}")
            return False
    
    def get_guild_channels(self):
        """الحصول على قنوات السيرفر"""
        url = f"{self.base_url}/guilds/{self.guild_id}/channels"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                channels = response.json()
                logger.info(f"✅ تم جلب {len(channels)} قناة")
                return channels
            else:
                logger.error(f"❌ خطأ في جلب القنوات: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ استثناء في جلب القنوات: {e}")
            return []
    
    def create_rules_embed(self, member_name, channel_name=None):
        """إنشاء رسالة القوانين"""
        embed = {
            "title": "🎮 **قوانين السيرفر** 🎮",
            "description": f"مرحباً {member_name} في روم **{channel_name or 'السيرفر'}**!\n\nيرجى الالتزام بالقوانين التالية:",
            "color": 5814783,  # الأزرق
            "fields": [],
            "footer": {
                "text": "تم الإرسال بواسطة بوت القوانين"
            },
            "thumbnail": {
                "url": "https://cdn.discordapp.com/embed/avatars/0.png"
            },
            "image": {
                "url": "https://i.imgur.com/3D-rules-example.png"
            }
        }
        
        # إضافة القوانين
        for rule in RULES:
            embed["fields"].append({
                "name": "📋",
                "value": rule,
                "inline": False
            })
        
        return embed
    
    def get_gateway(self):
        """الحصول على بوابة WebSocket"""
        url = f"{self.base_url}/gateway/bot"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                gateway_info = response.json()
                logger.info(f"✅ تم الحصول على البوابة: {gateway_info.get('url')}")
                return gateway_info
            else:
                logger.error(f"❌ خطأ في جلب البوابة: {response.status_code}")
                return None
        except Exception as e:
            logger.error(f"❌ استثناء في جلب البوابة: {e}")
            return None
    
    def send_heartbeat(self):
        """إرسال heartbeat"""
        if self.ws and self.heartbeat_interval:
            heartbeat_data = {
                "op": 1,
                "d": self.sequence
            }
            try:
                self.ws.send(json.dumps(heartbeat_data))
                logger.debug("💓 تم إرسال heartbeat")
            except Exception as e:
                logger.error(f"❌ خطأ في إرسال heartbeat: {e}")
    
    def send_identify(self):
        """إرسال identify"""
        identify_data = {
            "op": 2,
            "d": {
                "token": self.token,
                "intents": 1 << 7,  # GUILD_VOICE_STATES فقط
                "properties": {
                    "$os": "linux",
                    "$browser": "railway_bot",
                    "$device": "railway_bot"
                },
                "compress": False,
                "large_threshold": 250
            }
        }
        
        try:
            self.ws.send(json.dumps(identify_data))
            logger.info("🔐 تم إرسال identify")
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال identify: {e}")
    
    def handle_voice_state_update(self, data):
        """معالجة تحديثات حالة الصوت"""
        user_id = data.get("user_id")
        channel_id = data.get("channel_id")
        member = data.get("member", {})
        user = member.get("user", {})
        user_name = user.get("username", "مستخدم")
        
        # إذا دخل المستخدم روم صوتي (وليس الخروج)
        if channel_id and channel_id != self.last_voice_state.get(user_id):
            self.last_voice_state[user_id] = channel_id
            logger.info(f"🎤 المستخدم {user_name} دخل روم صوتي")
            
            # الحصول على قنوات السيرفر
            channels = self.get_guild_channels()
            
            # البحث عن روم القوانين أو روم عام
            rules_channel = None
            for channel in channels:
                if channel.get("name") in ["قوانين", "rules", "general", "القوانين"]:
                    if channel.get("type") == 0:  # text channel
                        rules_channel = channel
                        break
            
            if not rules_channel and channels:
                # أول قناة نصية
                for channel in channels:
                    if channel.get("type") == 0:
                        rules_channel = channel
                        break
            
            if rules_channel:
                # البحث عن اسم الروم الصوتي
                channel_name = "روم صوتي"
                for channel in channels:
                    if channel.get("id") == channel_id:
                        channel_name = channel.get("name", "روم صوتي")
                        break
                
                # إنشاء وإرسال رسالة القوانين
                embed = self.create_rules_embed(user_name, channel_name)
                self.send_message(rules_channel["id"], "", embed)
    
    def on_message(self, ws, message):
        """معالجة الرسائل الواردة"""
        try:
            data = json.loads(message)
            
            op = data.get("op")
            t = data.get("t")
            d = data.get("d")
            s = data.get("s")
            
            # تحديث الـ sequence
            if s:
                self.sequence = s
            
            logger.debug(f"📡 استقبلت: OP={op}, T={t}")
            
            if op == 10:  # Hello
                self.heartbeat_interval = d.get("heartbeat_interval") / 1000
                logger.info(f"📊 Heartbeat interval: {self.heartbeat_interval}ثانية")
                
                # بدء heartbeat timer
                def heartbeat_loop():
                    while self.running and self.ws:
                        time.sleep(self.heartbeat_interval)
                        if self.running and self.ws:
                            self.send_heartbeat()
                
                heartbeat_thread = threading.Thread(target=heartbeat_loop)
                heartbeat_thread.daemon = True
                heartbeat_thread.start()
                
                # إرسال identify
                self.send_identify()
                
            elif op == 11:  # Heartbeat ACK
                logger.debug("💓 Heartbeat ACK received")
                
            elif op == 0:  # Dispatch
                if t == "READY":
                    logger.info("✅ البوت جاهز ومتصل!")
                    logger.info(f"🤖 اسم البوت: {d.get('user', {}).get('username')}")
                    
                elif t == "VOICE_STATE_UPDATE":
                    self.handle_voice_state_update(d)
                    logger.info(f"🎤 حدث صوتي تم استقباله")
                    
                elif t == "GUILD_CREATE":
                    logger.info(f"🏠 انضمام للسيرفر: {d.get('name')}")
                    
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة الرسالة: {e}")
    
    def on_error(self, ws, error):
        """معالجة الأخطاء"""
        logger.error(f"❌ خطأ في WebSocket: {error}")
    
    def on_close(self, ws, close_status_code, close_msg):
        """معالجة إغلاق الاتصال"""
        logger.warning(f"🔌 WebSocket مغلق: {close_status_code} - {close_msg}")
        if self.running:
            logger.info("🔄 إعادة المحاولة بعد 10 ثواني...")
            threading.Timer(10.0, self.run_websocket).start()
    
    def on_open(self, ws):
        """عند فتح الاتصال"""
        logger.info("🔗 WebSocket مفتوح")
    
    def run_websocket(self):
        """تشغيل WebSocket للاستماع للأحداث"""
        gateway_info = self.get_gateway()
        if not gateway_info:
            logger.error("❌ لا يمكن الاتصال بالبوابة")
            return
        
        ws_url = gateway_info.get("url")
        if not ws_url:
            logger.error("❌ لم يتم العثور على رابط WebSocket")
            return
        
        # إضافة parameters
        ws_url += "?v=10&encoding=json"
        
        logger.info(f"🚀 الاتصال بـ: {ws_url}")
        
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_open=self.on_open,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close
        )
        
        try:
            self.ws.run_forever(ping_interval=20, ping_timeout=10)
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل WebSocket: {e}")
    
    def start(self):
        """بدء البوت"""
        logger.info("🚀 بدء تشغيل بوت ديسكورد...")
        
        if not self.token:
            logger.error("❌ DISCORD_TOKEN غير موجود!")
            return False
        
        if not self.guild_id:
            logger.error("❌ GUILD_ID غير موجود!")
            return False
        
        # اختبار الاتصال أولاً
        connected, bot_info = self.test_connection()
        if not connected:
            logger.error("❌ فشل الاتصال بـ Discord API")
            return False
        
        # بدء WebSocket في خيط منفصل
        ws_thread = threading.Thread(target=self.run_websocket)
        ws_thread.daemon = True
        ws_thread.start()
        
        logger.info("✅ البوت يعمل الآن!")
        return True

# تشغيل البوت
if __name__ == "__main__":
    bot = DiscordBot()
    if bot.start():
        # تشغيل خادم Flask
        app.run(host='0.0.0.0', port=8080)
    else:
        logger.error("❌ فشل بدء البوت")
