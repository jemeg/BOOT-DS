import requests
import json
import os
import time
import threading
import websocket
import logging
import hashlib
import secrets
from flask import Flask, jsonify, request, render_template_string, redirect, url_for, session, flash
from werkzeug.utils import secure_filename

# إعداد الـ logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# إعدادات البوت
BOT_TOKEN = os.getenv('DISCORD_TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')
GUILD_ID = os.getenv('GUILD_ID')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# إعدادات Flask
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET', secrets.token_hex(32))
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

# القوانين الافتراضية
DEFAULT_RULES = {
    "قوانين الأغرام": [
        "🚫 ممنوع السب والشتم",
        "🚫 ممنوع نشر محتوى غير لائق",
        "📝 احترام الجميع مطلوب",
        "💕 الالتزام بالآداب العامة"
    ],
    "قوانين الصحة": [
        "🏃 ممنوع الجري في الممرات",
        "🚫 ممنوع إزعاج الآخرين",
        "🧼 الحفاظ على نظافة المكان",
        "⚠️ إبلاغ الإدارة عن أي مشكلة"
    ],
    "قوانين الشرطة": [
        "🚓 عدم التسبب في مشاكل",
        "🚫 ممنوع حمل أسلحة",
        "👮 التعاون مع السلطات",
        "⚖️ الالتزام بالقوانين المحلية"
    ],
    "قوانين التعليم": [
        "📚 الاحترام المتبادل بين الطلاب والمعلمين",
        "🚫 ممنوع الغش في الامتحانات",
        "📱 إيقاف الهواتف أثناء الدروس",
        "🎯 المشاركة الفعالة في الأنشطة"
    ],
    "قوانين العمل": [
        "💼 الالتزام بمواعيد العمل",
        "🤝 التعاون مع الزملاء",
        "📊 إنجاز المهام في الوقت المحدد",
        "🏆 السعي نحو التميز"
    ],
    "قوانين الألعاب": [
        "🎮 اللعب النظيف والاحترافي",
        "🚫 ممنوع الغش",
        "🤝 احترام اللاعبين الآخرين",
        "🏆 قبول الهزيمة برياضة"
    ]
}

class UltimateRulesBot:
    def __init__(self):
        self.token = BOT_TOKEN
        self.base_url = "https://discord.com/api/v10"
        self.headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (Render, 1.0)"
        }
        self.ws = None
        self.running = False
        self.reconnect_attempts = 0
        self.max_reconnect_attempts = 5
        self.heartbeat_interval = 0
        self.last_heartbeat = 0
        self.sequence = 0
        self.session_id = None
        self.user_rules_messages = {}  # لتتبع رسائل القوانين لكل مستخدم
        self.settings = {
            "auto_send_on_join": True,
            "auto_delete_on_leave": True,
            "send_as_embed": True,
            "send_as_separate_messages": False,
            "delay_between_messages": 2,
            "enable_logging": True,
            "max_rules_per_message": 10
        }
        
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
    
    def send_rules_embed(self, channel_id, member_name=None, rules_title=None, rules_list=None, image_url=None, send_as_separate=False):
        """إرسال رسالة القوانين"""
        # استخدام القوانين المحددة أو الافتراضية
        if rules_title and rules_list:
            title = f"📜 {rules_title}"
            rules_text = '\n'.join([f"**{i+1}.** {rule}" for i, rule in enumerate(rules_list)])
        else:
            title = "📜 قوانين السيرفر"
            rules_text = '\n'.join([f"**{i+1}.** {rule}" for i, rule in enumerate(DEFAULT_RULES.get("قوانين الأغرام", []))])
        
        if send_as_separate and len(rules_list) > 1:
            # إرسال كل قانون في رسالة منفصلة
            message_ids = []
            for rule in rules_list:
                embed = {
                    "title": f"📜 {rules_title}",
                    "description": f"**القانون:** {rule}",
                    "color": 0x667eea,
                    "footer": {"text": f"مرحباً {member_name or 'بك'}!"}
                }
                
                if image_url and rules_list.index(rule) == 0:
                    embed["image"] = {"url": image_url}
                
                url = f"{self.base_url}/channels/{channel_id}/messages"
                data = {"embeds": [embed]}
                
                try:
                    response = requests.post(url, headers=self.headers, json=data, timeout=10)
                    if response.status_code == 200:
                        result = response.json()
                        message_ids.append(result.get('id'))
                        time.sleep(self.settings["delay_between_messages"])
                    else:
                        logger.error(f"❌ خطأ في إرسال رسالة القانون: {response.status_code}")
                        return False, response.text
                except Exception as e:
                    logger.error(f"❌ استثناء في إرسال رسالة القانون: {e}")
                    return False, str(e)
            
            logger.info(f"✅ تم إرسال {len(message_ids)} رسالة قوانين بنجاح")
            return True, message_ids
        else:
            # إرسال في رسالة واحدة
            embed = {
                "title": title,
                "description": f"مرحباً بك في السيرفر! يرجى قراءة القوانين أدناه:\n\n{rules_text}",
                "color": 0x667eea,
                "footer": {"text": f"مرحباً {member_name or 'بك'}!"}
            }
            
            # إضافة الصورة إذا كانت موجودة
            if image_url:
                embed["image"] = {"url": image_url}
            
            url = f"{self.base_url}/channels/{channel_id}/messages"
            data = {"embeds": [embed]}
            
            try:
                response = requests.post(url, headers=self.headers, json=data, timeout=10)
                if response.status_code == 200:
                    result = response.json()
                    logger.info(f"✅ تم إرسال رسالة القوانين بنجاح")
                    return True, result
                else:
                    logger.error(f"❌ خطأ في إرسال رسالة القوانين: {response.status_code}")
                    return False, response.text
            except Exception as e:
                logger.error(f"❌ استثناء في إرسال رسالة القوانين: {e}")
                return False, str(e)
    
    def send_text_message(self, channel_id, content):
        """إرسال رسالة نصية"""
        url = f"{self.base_url}/channels/{channel_id}/messages"
        data = {"content": content}
        
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=10)
            if response.status_code == 200:
                result = response.json()
                logger.info(f"✅ تم إرسال الرسالة النصية بنجاح")
                return True, result
            else:
                logger.error(f"❌ خطأ في إرسال الرسالة النصية: {response.status_code}")
                return False, response.text
        except Exception as e:
            logger.error(f"❌ استثناء في إرسال الرسالة النصية: {e}")
            return False, str(e)
    
    def delete_message(self, channel_id, message_id):
        """حذف رسالة"""
        url = f"{self.base_url}/channels/{channel_id}/messages/{message_id}"
        try:
            response = requests.delete(url, headers=self.headers, timeout=10)
            if response.status_code == 204:
                logger.info(f"✅ تم حذف الرسالة بنجاح")
                return True
            else:
                logger.error(f"❌ خطأ في حذف الرسالة: {response.status_code}")
                return False
        except Exception as e:
            logger.error(f"❌ استثناء في حذف الرسالة: {e}")
            return False
    
    def update_settings(self, new_settings):
        """تحديث إعدادات البوت"""
        self.settings.update(new_settings)
        logger.info(f"✅ تم تحديث إعدادات البوت: {new_settings}")
    
    def get_user_guilds(self):
        """الحصول على السيرفرات"""
        url = f"{self.base_url}/users/@me/guilds"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                guilds = response.json()
                logger.info(f"✅ تم جلب {len(guilds)} سيرفر")
                return guilds
            else:
                logger.error(f"❌ خطأ في جلب السيرفرات: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ استثناء في جلب السيرفرات: {e}")
            return []
    
    def get_guild_channels(self, guild_id):
        """الحصول على قنوات السيرفر"""
        url = f"{self.base_url}/guilds/{guild_id}/channels"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                channels = response.json()
                logger.info(f"✅ تم جلب {len(channels)} قناة من السيرفر {guild_id}")
                return channels
            else:
                logger.error(f"❌ خطأ في جلب القنوات: {response.status_code}")
                return []
        except Exception as e:
            logger.error(f"❌ استثناء في جلب القنوات: {e}")
            return []

class UltimateWebSocket:
    def __init__(self, bot):
        self.bot = bot
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
            gateway_url = "wss://gateway.discord.gg/?v=10&encoding=json"
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
                "token": self.bot.token,
                "intents": 513,  # GUILDS (1) + GUILD_VOICE_STATES (512)
                "properties": {
                    "os": "linux",
                    "browser": "ultimate_rules_bot",
                    "device": "ultimate_rules_bot"
                }
            }
        }
        
        if self.session_id:
            # Resume إذا كان لدينا session_id
            identify_payload = {
                "op": 6,
                "d": {
                    "token": self.bot.token,
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
            
            if not user_id or not channel_id:
                return
            
            # فقط للقنوات الصوتية
            if data.get('channel_id') is None:
                # المستخدم خرج من القناة الصوتية
                self.handle_user_leave(user_id, channel_id, username)
            else:
                # المستخدم دخل قناة صوتية
                self.handle_user_join(user_id, channel_id, username)
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة تحديث الصوت: {e}")
    
    def handle_user_join(self, user_id, channel_id, username):
        """معالجة دخول المستخدم للقناة الصوتية"""
        try:
            if not self.bot.settings["auto_send_on_join"]:
                return
            
            # مفتاح لتتبع رسائل المستخدم
            user_key = f"{user_id}_{channel_id}"
            
            # إرسال رسالة القوانين عند دخول القناة
            if channel_id not in self.bot.user_rules_messages:
                self.bot.user_rules_messages[channel_id] = {}
            
            # إرسال رسالة القوانين
            success, result = self.bot.send_rules_embed(
                channel_id, 
                username, 
                None, 
                DEFAULT_RULES.get("قوانين الأغرام", []),
                None,
                self.bot.settings["send_as_separate_messages"]
            )
            
            if success:
                if isinstance(result, list):
                    # إذا كانت رسائل متعددة
                    self.bot.user_rules_messages[channel_id][user_id] = result
                else:
                    # إذا كانت رسالة واحدة
                    message_id = result.get('id')
                    self.bot.user_rules_messages[channel_id][user_id] = [message_id]
                
                logger.info(f"📜 تم إرسال قوانين للمستخدم {username} في القناة {channel_id}")
            else:
                logger.error(f"❌ فشل في إرسال القوانين: {result}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة دخول المستخدم: {e}")
    
    def handle_user_leave(self, user_id, channel_id, username):
        """معالجة خروج المستخدم من القناة الصوتية"""
        try:
            if not self.bot.settings["auto_delete_on_leave"]:
                return
            
            # حذف رسالة القوانين عند خروج المستخدم
            if channel_id in self.bot.user_rules_messages:
                if user_id in self.bot.user_rules_messages[channel_id]:
                    message_ids = self.bot.user_rules_messages[channel_id][user_id]
                    
                    # حذف جميع الرسائل
                    deleted_count = 0
                    for message_id in message_ids:
                        if self.bot.delete_message(channel_id, message_id):
                            deleted_count += 1
                    
                    if deleted_count > 0:
                        del self.bot.user_rules_messages[channel_id][user_id]
                        logger.info(f"🗑️ تم حذف {deleted_count} رسالة قوانين للمستخدم {username}")
                    else:
                        logger.error(f"❌ فشل في حذف رسائل القوانين")
                        
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة خروج المستخدم: {e}")

# إنشاء كائن البوت
bot = UltimateRulesBot()
ultimate_websocket = UltimateWebSocket(bot)

# HTML Templates
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول - لوحة تحكم القوانين النهائية</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .login-container {
            background: white;
            padding: 40px;
            border-radius: 15px;
            box-shadow: 0 15px 35px rgba(0,0,0,0.1);
            width: 100%;
            max-width: 400px;
        }
        h1 { text-align: center; color: #333; margin-bottom: 30px; font-size: 28px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #555; font-weight: 500; }
        input[type="password"] {
            width: 100%; padding: 12px; border: 2px solid #ddd; border-radius: 8px;
            font-size: 16px; transition: border-color 0.3s;
        }
        input[type="password"]:focus { outline: none; border-color: #667eea; }
        .btn {
            width: 100%; padding: 12px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white; border: none; border-radius: 8px; font-size: 16px; font-weight: 600;
            cursor: pointer; transition: transform 0.2s;
        }
        .btn:hover { transform: translateY(-2px); }
        .alert { padding: 12px; border-radius: 8px; margin-bottom: 20px; text-align: center; }
        .alert-danger { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .bot-info { text-align: center; margin-top: 20px; color: #666; font-size: 14px; }
        .status-indicator {
            display: inline-block;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            margin-left: 10px;
        }
        .status-online { background: #28a745; }
        .status-offline { background: #dc3545; }
    </style>
</head>
<body>
    <div class="login-container">
        <h1>📜 لوحة تحكم القوانين النهائية</h1>
        <div style="text-align: center; margin-bottom: 20px;">
            <span>حالة البوت:</span>
            <span class="status-indicator status-online" id="botStatus"></span>
            <span id="statusText">متصل</span>
        </div>
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert alert-danger">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        <form method="POST" action="/login">
            <div class="form-group">
                <label for="password">كلمة المرور:</label>
                <input type="password" id="password" name="password" required>
            </div>
            <button type="submit" class="btn">تسجيل الدخول</button>
        </form>
        <div class="bot-info"><p>لوحة تحكم بوت القوانين النهائي</p></div>
    </div>
    
    <script>
        // فحص حالة البوت
        fetch('/api/bot-status')
            .then(response => response.json())
            .then(data => {
                const statusIndicator = document.getElementById('botStatus');
                const statusText = document.getElementById('statusText');
                
                if (data.connected) {
                    statusIndicator.className = 'status-indicator status-online';
                    statusText.textContent = 'متصل';
                } else {
                    statusIndicator.className = 'status-indicator status-offline';
                    statusText.textContent = 'غير متصل';
                }
            })
            .catch(error => {
                console.error('Error checking bot status:', error);
            });
    </script>
</body>
</html>
"""

ULTIMATE_DASHBOARD = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم القوانين النهائية</title>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f6fa;
            min-height: 100vh;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px 0;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header-content {
            max-width: 1400px;
            margin: 0 auto;
            padding: 0 20px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .header h1 { font-size: 28px; }
        .logout-btn {
            background: rgba(255,255,255,0.2);
            color: white;
            border: 1px solid rgba(255,255,255,0.3);
            padding: 8px 16px;
            border-radius: 6px;
            text-decoration: none;
            transition: background 0.3s;
        }
        .logout-btn:hover { background: rgba(255,255,255,0.3); }
        .container { max-width: 1400px; margin: 0 auto; padding: 20px; }
        .card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            overflow: hidden;
            margin-bottom: 20px;
        }
        .card-header {
            background: #667eea;
            color: white;
            padding: 20px;
            font-size: 18px;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .card-body { padding: 25px; }
        .form-group { margin-bottom: 20px; }
        label { display: block; margin-bottom: 8px; color: #333; font-weight: 500; }
        select, textarea, input[type="text"], input[type="number"], input[type="file"] {
            width: 100%;
            padding: 12px;
            border: 2px solid #ddd;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        select:focus, textarea:focus, input:focus {
            outline: none;
            border-color: #667eea;
        }
        textarea { resize: vertical; min-height: 120px; }
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 8px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s;
            margin-left: 10px;
        }
        .btn:hover { transform: translateY(-2px); }
        .btn-secondary {
            background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
        }
        .btn-success {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
        }
        .rules-categories {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .category-card {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
        }
        .category-title {
            font-size: 16px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 15px;
        }
        .category-btn {
            width: 100%;
            padding: 10px;
            margin-bottom: 10px;
            background: white;
            border: 2px solid #667eea;
            color: #667eea;
            border-radius: 6px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .category-btn:hover {
            background: #667eea;
            color: white;
        }
        .category-btn.selected {
            background: #667eea;
            color: white;
        }
        .alert {
            padding: 12px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        .alert-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .alert-danger {
            background: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 25px;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            text-align: center;
        }
        .stat-number {
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }
        .stat-label { color: #666; font-size: 14px; }
        .websocket-status {
            background: #28a745;
            color: white;
            padding: 10px;
            border-radius: 6px;
            text-align: center;
            margin-bottom: 20px;
        }
        .websocket-status.disconnected {
            background: #dc3545;
        }
        .settings-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
        }
        .setting-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #dee2e6;
        }
        .setting-label {
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
        }
        .switch {
            position: relative;
            display: inline-block;
            width: 60px;
            height: 34px;
        }
        .switch input { opacity: 0; width: 0; height: 0; }
        .slider {
            position: absolute;
            cursor: pointer;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background-color: #ccc;
            transition: .4s;
            border-radius: 34px;
        }
        .slider:before {
            position: absolute;
            content: "";
            height: 26px;
            width: 26px;
            left: 4px;
            bottom: 4px;
            background-color: white;
            transition: .4s;
            border-radius: 50%;
        }
        input:checked + .slider {
            background-color: #667eea;
        }
        input:checked + .slider:before {
            transform: translateX(26px);
        }
        .tabs {
            display: flex;
            border-bottom: 2px solid #dee2e6;
            margin-bottom: 20px;
        }
        .tab {
            padding: 12px 20px;
            cursor: pointer;
            border: none;
            background: none;
            font-size: 16px;
            font-weight: 500;
            color: #666;
            transition: all 0.3s;
        }
        .tab.active {
            color: #667eea;
            border-bottom: 2px solid #667eea;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
        .two-column {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
        }
        .image-preview {
            max-width: 200px;
            max-height: 200px;
            margin: 10px auto;
            border-radius: 8px;
            border: 2px solid #ddd;
            display: block;
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1>📜 لوحة تحكم القوانين النهائية</h1>
            <a href="/logout" class="logout-btn">تسجيل الخروج</a>
        </div>
    </div>
    
    <div class="container">
        {% with messages = get_flashed_messages() %}
            {% if messages %}
                {% for message in messages %}
                    <div class="alert alert-{{ 'success' if 'success' in message.lower() else 'danger' }}">{{ message }}</div>
                {% endfor %}
            {% endif %}
        {% endwith %}
        
        <div class="websocket-status" id="wsStatus">
            <i class="fas fa-wifi"></i> WebSocket: <span id="wsStatusText">متصل</span>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_servers }}</div>
                <div class="stat-label">السيرفرات</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_channels }}</div>
                <div class="stat-label">القنوات</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.rules_count }}</div>
                <div class="stat-label">فئات القوانين</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.active_rules }}</div>
                <div class="stat-label">القوانين النشطة</div>
            </div>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('send-rules')">إرسال القوانين</button>
            <button class="tab" onclick="showTab('settings')">الإعدادات</button>
            <button class="tab" onclick="showTab('categories')">إدارة الفئات</button>
        </div>
        
        <!-- تبويب إرسال القوانين -->
        <div id="send-rules" class="tab-content active">
            <div class="card">
                <div class="card-header">
                    <i class="fas fa-paper-plane"></i>
                    إرسال رسالة القوانين
                </div>
                <div class="card-body">
                    <div class="two-column">
                        <div>
                            <div class="form-group">
                                <label>اختر السيرفر:</label>
                                <select id="serverSelect" onchange="loadChannels()">
                                    <option value="">اختر السيرفر...</option>
                                    {% for server in servers %}
                                    <option value="{{ server.id }}">{{ server.name }}</option>
                                    {% endfor %}
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label>اختر القناة:</label>
                                <select id="channelSelect" disabled>
                                    <option value="">اختر القناة...</option>
                                </select>
                            </div>
                            
                            <div class="form-group">
                                <label>اسم المستخدم (اختياري):</label>
                                <input type="text" id="memberName" placeholder="اكتب اسم المستخدم...">
                            </div>
                        </div>
                        
                        <div>
                            <div class="form-group">
                                <label>صورة القوانين (اختياري):</label>
                                <input type="file" id="rulesImage" accept="image/*" onchange="previewImage(event)">
                                <img id="imagePreview" class="image-preview" style="display: none;">
                            </div>
                            
                            <div class="form-group">
                                <label>طريقة الإرسال:</label>
                                <select id="sendMethod">
                                    <option value="single">رسالة واحدة</option>
                                    <option value="separate">رسائل منفصلة</option>
                                </select>
                            </div>
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label>رسالة مخصصة (اختياري):</label>
                        <textarea id="customMessage" placeholder="اكتب رسالة مخصصة هنا..."></textarea>
                    </div>
                    
                    <button class="btn" onclick="sendRules()">
                        <i class="fas fa-paper-plane"></i> إرسال القوانين
                    </button>
                    <button class="btn btn-secondary" onclick="sendCustomMessage()">
                        <i class="fas fa-comment"></i> إرسال رسالة مخصصة
                    </button>
                </div>
            </div>
        </div>
        
        <!-- تبويب الإعدادات -->
        <div id="settings" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <i class="fas fa-cog"></i>
                    إعدادات البوت
                </div>
                <div class="card-body">
                    <div class="settings-grid">
                        <div class="setting-item">
                            <div class="setting-label">إرسال تلقائي عند الدخول</div>
                            <label class="switch">
                                <input type="checkbox" id="autoSendOnJoin" checked>
                                <span class="slider"></span>
                            </label>
                        </div>
                        
                        <div class="setting-item">
                            <div class="setting-label">حذف تلقائي عند الخروج</div>
                            <label class="switch">
                                <input type="checkbox" id="autoDeleteOnLeave" checked>
                                <span class="slider"></span>
                            </label>
                        </div>
                        
                        <div class="setting-item">
                            <div class="setting-label">إرسال كـ Embed</div>
                            <label class="switch">
                                <input type="checkbox" id="sendAsEmbed" checked>
                                <span class="slider"></span>
                            </label>
                        </div>
                        
                        <div class="setting-item">
                            <div class="setting-label">تفعيل التسجيل</div>
                            <label class="switch">
                                <input type="checkbox" id="enableLogging" checked>
                                <span class="slider"></span>
                            </label>
                        </div>
                        
                        <div class="setting-item">
                            <div class="setting-label">المدة بين الرسائل (ثواني)</div>
                            <input type="number" id="delayBetweenMessages" value="2" min="1" max="10">
                        </div>
                        
                        <div class="setting-item">
                            <div class="setting-label">أقصى عدد قوانين في الرسالة</div>
                            <input type="number" id="maxRulesPerMessage" value="10" min="1" max="50">
                        </div>
                    </div>
                    
                    <button class="btn btn-success" onclick="saveSettings()">
                        <i class="fas fa-save"></i> حفظ الإعدادات
                    </button>
                </div>
            </div>
        </div>
        
        <!-- تبويب إدارة الفئات -->
        <div id="categories" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <i class="fas fa-list"></i>
                    فئات القوانين
                </div>
                <div class="card-body">
                    <div class="rules-categories">
                        {% for category, rules in rules.items() %}
                        <div class="category-card">
                            <div class="category-title">{{ category }}</div>
                            <button class="category-btn" onclick="selectCategory('{{ category }}', {{ rules|tojson }})">
                                <i class="fas fa-list"></i> عرض القوانين
                            </button>
                            <button class="category-btn" onclick="editCategory('{{ category }}', {{ rules|tojson }})">
                                <i class="fas fa-edit"></i> تعديل
                            </button>
                        </div>
                        {% endfor %}
                    </div>
                    
                    <button class="btn" onclick="addNewCategory()">
                        <i class="fas fa-plus"></i> إضافة فئة جديدة
                    </button>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let servers = {{ servers|tojson }};
        let channels = {};
        let selectedCategory = null;
        let selectedRules = [];
        let currentSettings = {{ settings|tojson }};
        
        function showTab(tabName) {
            // إخفاء جميع التبويبات
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // إظهار التبويب المحدد
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        function loadChannels() {
            const serverId = document.getElementById('serverSelect').value;
            const channelSelect = document.getElementById('channelSelect');
            
            if (!serverId) {
                channelSelect.innerHTML = '<option value="">اختر القناة...</option>';
                channelSelect.disabled = true;
                return;
            }
            
            fetch(`/api/servers/${serverId}/channels`)
                .then(response => response.json())
                .then(data => {
                    channels = data;
                    const textChannels = channels.filter(ch => ch.type === 0);
                    channelSelect.innerHTML = textChannels.map(ch => 
                        `<option value="${ch.id}">#${ch.name}</option>`
                    ).join('');
                    channelSelect.disabled = false;
                })
                .catch(error => {
                    console.error('Error loading channels:', error);
                });
        }
        
        function selectCategory(category, rules) {
            // إزالة التحديد من جميع الأزرار
            document.querySelectorAll('.category-btn').forEach(btn => {
                btn.classList.remove('selected');
            });
            
            // إضافة التحديد للزر المضغوط عليه
            event.target.classList.add('selected');
            
            selectedCategory = category;
            selectedRules = rules;
            
            alert(`تم اختيار فئة "${category}"`);
        }
        
        function editCategory(category, rules) {
            alert(`تعديل فئة "${category}" - هذه الميزة قيد التطوير`);
        }
        
        function addNewCategory() {
            alert(`إضافة فئة جديدة - هذه الميزة قيد التطوير`);
        }
        
        function previewImage(event) {
            const file = event.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(e) {
                    const preview = document.getElementById('imagePreview');
                    preview.src = e.target.result;
                    preview.style.display = 'block';
                };
                reader.readAsDataURL(file);
            }
        }
        
        function sendRules() {
            const channelId = document.getElementById('channelSelect').value;
            const memberName = document.getElementById('memberName').value;
            const sendMethod = document.getElementById('sendMethod').value;
            const customMessage = document.getElementById('customMessage').value;
            
            if (!channelId) {
                alert('يرجى اختيار القناة أولاً');
                return;
            }
            
            if (!selectedCategory && !customMessage) {
                alert('يرجى اختيار فئة القوانين أو كتابة رسالة مخصصة');
                return;
            }
            
            const data = {
                channel_id: channelId,
                member_name: memberName,
                send_as_separate: sendMethod === 'separate'
            };
            
            if (selectedCategory) {
                data.rules_title = selectedCategory;
                data.rules_list = selectedRules;
            }
            
            if (customMessage) {
                data.custom_message = customMessage;
            }
            
            fetch('/api/send-ultimate-rules', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('تم إرسال القوانين بنجاح!');
                } else {
                    alert('خطأ: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('حدث خطأ أثناء إرسال القوانين');
            });
        }
        
        function sendCustomMessage() {
            const channelId = document.getElementById('channelSelect').value;
            const customMessage = document.getElementById('customMessage').value;
            
            if (!channelId) {
                alert('يرجى اختيار القناة أولاً');
                return;
            }
            
            if (!customMessage) {
                alert('يرجى كتابة رسالة مخصصة');
                return;
            }
            
            fetch('/api/send-custom-message', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    channel_id: channelId,
                    content: customMessage
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('تم إرسال الرسالة بنجاح!');
                } else {
                    alert('خطأ: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('حدث خطأ أثناء إرسال الرسالة');
            });
        }
        
        function saveSettings() {
            const settings = {
                auto_send_on_join: document.getElementById('autoSendOnJoin').checked,
                auto_delete_on_leave: document.getElementById('autoDeleteOnLeave').checked,
                send_as_embed: document.getElementById('sendAsEmbed').checked,
                enable_logging: document.getElementById('enableLogging').checked,
                delay_between_messages: parseInt(document.getElementById('delayBetweenMessages').value),
                max_rules_per_message: parseInt(document.getElementById('maxRulesPerMessage').value)
            };
            
            fetch('/api/update-settings', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(settings)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    alert('تم حفظ الإعدادات بنجاح!');
                } else {
                    alert('خطأ: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('حدث خطأ أثناء حفظ الإعدادات');
            });
        }
        
        // فحص حالة WebSocket
        function updateWebSocketStatus() {
            fetch('/api/websocket-status')
                .then(response => response.json())
                .then(data => {
                    const wsStatus = document.getElementById('wsStatus');
                    const wsStatusText = document.getElementById('wsStatusText');
                    
                    if (data.connected) {
                        wsStatus.classList.remove('disconnected');
                        wsStatusText.textContent = 'متصل';
                    } else {
                        wsStatus.classList.add('disconnected');
                        wsStatusText.textContent = 'غير متصل';
                    }
                })
                .catch(error => {
                    console.error('Error checking WebSocket status:', error);
                });
        }
        
        // تحديث حالة WebSocket كل 5 ثواني
        setInterval(updateWebSocketStatus, 5000);
        
        // تحديث الحالة فوراً
        updateWebSocketStatus();
    </script>
</body>
</html>
"""

# Routes
@app.route('/')
def index():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        password = request.form.get('password')
        if hashlib.sha256(password.encode()).hexdigest() == hashlib.sha256(ADMIN_PASSWORD.encode()).hexdigest():
            session['logged_in'] = True
            session.permanent = True
            flash('تم تسجيل الدخول بنجاح!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('كلمة المرور غير صحيحة!', 'danger')
    return render_template_string(LOGIN_TEMPLATE)

@app.route('/logout')
def logout():
    session.clear()
    flash('تم تسجيل الخروج بنجاح!', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    if 'logged_in' not in session:
        return redirect(url_for('login'))
    
    # الحصول على السيرفرات
    guilds = bot.get_user_guilds()
    
    # حساب الإحصائيات
    total_servers = len(guilds)
    total_channels = 0
    active_rules = 0
    
    for guild in guilds:
        channels = bot.get_guild_channels(guild['id'])
        total_channels += len(channels)
    
    for category, rules in DEFAULT_RULES.items():
        active_rules += len(rules)
    
    stats = {
        'total_servers': total_servers,
        'total_channels': total_channels,
        'rules_count': len(DEFAULT_RULES),
        'active_rules': active_rules
    }
    
    return render_template_string(ULTIMATE_DASHBOARD, 
                              servers=guilds, 
                              stats=stats, 
                              rules=DEFAULT_RULES,
                              settings=bot.settings)

@app.route('/api/servers/<server_id>/channels')
def api_server_channels(server_id):
    if 'logged_in' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    channels = bot.get_guild_channels(server_id)
    return jsonify(channels)

@app.route('/api/send-ultimate-rules', methods=['POST'])
def api_send_ultimate_rules():
    if 'logged_in' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    
    try:
        data = request.get_json()
        channel_id = data.get('channel_id')
        member_name = data.get('member_name', '')
        rules_title = data.get('rules_title')
        rules_list = data.get('rules_list')
        custom_message = data.get('custom_message')
        send_as_separate = data.get('send_as_separate', False)
        
        if not channel_id:
            return jsonify({'success': False, 'error': 'لم يتم تحديد القناة'})
        
        if custom_message:
            # إرسال رسالة مخصصة
            success, result = bot.send_text_message(channel_id, custom_message)
        else:
            # إرسال القوانين
            if not rules_title:
                return jsonify({'success': False, 'error': 'لم يتم تحديد فئة القوانين'})
            
            success, result = bot.send_rules_embed(
                channel_id, 
                member_name, 
                rules_title, 
                rules_list,
                None,
                send_as_separate
            )
        
        if success:
            return jsonify({'success': True, 'message_id': result.get('id') if isinstance(result, dict) else result})
        else:
            return jsonify({'success': False, 'error': str(result)})
    except Exception as e:
        logger.error(f"Error in send_ultimate_rules API: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/send-custom-message', methods=['POST'])
def api_send_custom_message():
    if 'logged_in' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    
    try:
        data = request.get_json()
        channel_id = data.get('channel_id')
        content = data.get('content')
        
        if not channel_id or not content:
            return jsonify({'success': False, 'error': 'لم يتم تحديد القناة أو المحتوى'})
        
        success, result = bot.send_text_message(channel_id, content)
        
        if success:
            return jsonify({'success': True, 'message_id': result.get('id')})
        else:
            return jsonify({'success': False, 'error': str(result)})
    except Exception as e:
        logger.error(f"Error in send_custom_message API: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/update-settings', methods=['POST'])
def api_update_settings():
    if 'logged_in' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    
    try:
        data = request.get_json()
        bot.update_settings(data)
        return jsonify({'success': True, 'settings': bot.settings})
    except Exception as e:
        logger.error(f"Error in update_settings API: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/bot-status')
def api_bot_status():
    """فحص حالة البوت"""
    connected, _ = bot.test_connection()
    return jsonify({
        'connected': connected,
        'timestamp': time.time()
    })

@app.route('/api/websocket-status')
def api_websocket_status():
    """فحص حالة WebSocket"""
    return jsonify({
        'connected': ultimate_websocket.running,
        'timestamp': time.time()
    })

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": time.time()})

@app.route('/test')
def test():
    return jsonify({
        "token_exists": bool(BOT_TOKEN),
        "token_length": len(BOT_TOKEN) if BOT_TOKEN else 0,
        "bot_connected": bot.test_connection()[0],
        "websocket_connected": ultimate_websocket.running,
        "rules_count": len(DEFAULT_RULES),
        "settings": bot.settings
    })

if __name__ == "__main__":
    # اختبار الاتصال
    connected, bot_info = bot.test_connection()
    if connected:
        logger.info("✅ بوت القوانين النهائي متصل وجاهز للعمل")
        
        # بدء WebSocket للمراقبة
        try:
            if ultimate_websocket.connect():
                logger.info("✅ WebSocket للقوانين بدأ العمل")
        except Exception as e:
            logger.error(f"❌ خطأ في بدء WebSocket: {e}")
        
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 3000)), debug=False)
    else:
        logger.error("❌ فشل الاتصال بالبوت")
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 3000)), debug=False)
