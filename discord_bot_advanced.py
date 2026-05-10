import requests
import json
import os
import time
import threading
from flask import Flask, jsonify, request
import websocket
import logging

# إعداد الـ logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# إعدادات البوت
BOT_TOKEN = os.getenv('DISCORD_TOKEN')
APPLICATION_ID = os.getenv('APPLICATION_ID')
GUILD_ID = os.getenv('GUILD_ID')

# قائمة القوانين الافتراضية
DEFAULT_RULES = [
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
    return "بوت ديسكورد المتقدم يعمل!"

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

class ChannelContent:
    """إدارة المحتوى لكل قناة"""
    def __init__(self):
        self.channels_data = {}
        self.load_data()
    
    def load_data(self):
        """تحميل البيانات من ملف"""
        try:
            if os.path.exists('channels_data.json'):
                with open('channels_data.json', 'r', encoding='utf-8') as f:
                    self.channels_data = json.load(f)
                    logger.info(f"✅ تم تحميل بيانات {len(self.channels_data)} قناة")
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل البيانات: {e}")
            self.channels_data = {}
    
    def save_data(self):
        """حفظ البيانات في ملف"""
        try:
            with open('channels_data.json', 'w', encoding='utf-8') as f:
                json.dump(self.channels_data, f, ensure_ascii=False, indent=2)
            logger.info("✅ تم حفظ بيانات القنوات")
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ البيانات: {e}")
    
    def set_channel_content(self, channel_id, channel_name, content_type, content_data):
        """تعيين محتوى لقناة معينة"""
        if channel_id not in self.channels_data:
            self.channels_data[channel_id] = {
                'name': channel_name,
                'created_at': time.time()
            }
        
        self.channels_data[channel_id].update({
            'content_type': content_type,
            'content_data': content_data,
            'updated_at': time.time()
        })
        
        self.save_data()
        logger.info(f"✅ تم تعيين محتوى لقناة {channel_name}")
    
    def get_channel_content(self, channel_id):
        """الحصول على محتوى قناة معينة"""
        return self.channels_data.get(channel_id, {})
    
    def get_all_channels(self):
        """الحصول على كل القنوات"""
        return self.channels_data

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
        self.channel_content = ChannelContent()
        
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
    
    def send_message(self, channel_id, content, embed=None, components=None):
        """إرسال رسالة إلى قناة"""
        url = f"{self.base_url}/channels/{channel_id}/messages"
        data = {"content": content}
        
        if embed:
            data["embeds"] = [embed]
        
        if components:
            data["components"] = components
            
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
    
    def create_content_embed(self, channel_data, member_name=None):
        """إنشاء رسالة محتوى مخصصة"""
        content_type = channel_data.get('content_type', 'text')
        content_data = channel_data.get('content_data', {})
        
        if content_type == 'rules':
            embed = {
                "title": content_data.get('title', '🎮 **قوانين السيرفر** 🎮'),
                "description": content_data.get('description', f"مرحباً {member_name or 'بك'}!\n\nيرجى الالتزام بالقوانين التالية:"),
                "color": content_data.get('color', 5814783),
                "fields": [],
                "footer": {"text": content_data.get('footer', 'تم الإرسال بواسطة بوت القوانين')},
                "thumbnail": {"url": content_data.get('thumbnail', 'https://cdn.discordapp.com/embed/avatars/0.png')},
                "image": {"url": content_data.get('image', 'https://i.imgur.com/3D-rules-example.png')}
            }
            
            rules = content_data.get('rules', DEFAULT_RULES)
            for rule in rules:
                embed["fields"].append({
                    "name": "📋",
                    "value": rule,
                    "inline": False
                })
                
        elif content_type == 'welcome':
            embed = {
                "title": content_data.get('title', '🎉 **أهلاً وسهلاً** 🎉'),
                "description": content_data.get('description', f"مرحباً {member_name or 'بك'} في السيرفر!"),
                "color": content_data.get('color', 65280),
                "fields": [],
                "footer": {"text": content_data.get('footer', 'تم الإرسال بواسطة بوت الترحيب')},
                "thumbnail": {"url": content_data.get('thumbnail', 'https://cdn.discordapp.com/embed/avatars/0.png')},
                "image": {"url": content_data.get('image', 'https://i.imgur.com/welcome-example.png')}
            }
            
            welcome_messages = content_data.get('messages', ['🎊 أهلاً بك في السيرفر!'])
            for msg in welcome_messages:
                embed["fields"].append({
                    "name": "💫",
                    "value": msg,
                    "inline": False
                })
                
        elif content_type == 'announcement':
            embed = {
                "title": content_data.get('title', '📢 **إعلان هام** 📢'),
                "description": content_data.get('description', 'إعلان مهم لجميع الأعضاء'),
                "color": content_data.get('color', 15158332),
                "fields": [],
                "footer": {"text": content_data.get('footer', 'تم الإرسال بواسطة بوت الإعلانات')},
                "thumbnail": {"url": content_data.get('thumbnail', 'https://cdn.discordapp.com/embed/avatars/0.png')},
                "image": {"url": content_data.get('image', 'https://i.imgur.com/announcement-example.png')}
            }
            
            announcements = content_data.get('announcements', ['📌 إعلان جديد'])
            for announcement in announcements:
                embed["fields"].append({
                    "name": "📋",
                    "value": announcement,
                    "inline": False
                })
                
        else:  # text or custom
            embed = {
                "title": content_data.get('title', ''),
                "description": content_data.get('description', ''),
                "color": content_data.get('color', 3447003),
                "fields": [],
                "footer": {"text": content_data.get('footer', 'تم الإرسال بواسطة البوت')},
                "thumbnail": {"url": content_data.get('thumbnail', '')},
                "image": {"url": content_data.get('image', '')}
            }
            
            custom_fields = content_data.get('fields', [])
            for field in custom_fields:
                embed["fields"].append({
                    "name": field.get('name', ''),
                    "value": field.get('value', ''),
                    "inline": field.get('inline', False)
                })
        
        # إزالة الحقول الفارغة
        if not embed["thumbnail"]["url"]:
            del embed["thumbnail"]
        if not embed["image"]["url"]:
            del embed["image"]
        if not embed["fields"]:
            del embed["fields"]
            
        return embed
    
    def handle_message_create(self, data):
        """معالجة إنشاء الرسائل (للأوامر)"""
        channel_id = data.get("channel_id")
        author = data.get("author", {})
        content = data.get("content", "")
        
        # تجاهل رسائل البوت
        if author.get("bot"):
            return
        
        # التحقق من الأوامر
        if content.startswith('!'):
            self.handle_command(channel_id, author, content)
    
    def handle_command(self, channel_id, author, content):
        """معالجة أوامر البوت"""
        parts = content.split(' ', 1)
        command = parts[0].lower()
        args = parts[1] if len(parts) > 1 else ''
        
        # التحقق من صلاحيات المشرف
        is_admin = self.is_admin(author)
        
        if command == '!مساعدة':
            self.show_help(channel_id)
        elif command == '!قائمة_الرومات':
            self.show_channels_list(channel_id)
        elif command == '!إعدادات_الروم':
            if args:
                self.show_channel_settings(channel_id, args.strip())
            else:
                self.show_current_channel_settings(channel_id)
        elif command == '!تعيين_محتوى' and is_admin:
            self.set_channel_content_command(channel_id, args)
        elif command == '!مسح_المحتوى' and is_admin:
            self.clear_channel_content_command(channel_id, args)
    
    def is_admin(self, author):
        """التحقق مما إذا كان المستخدم مشرف"""
        # هنا يمكنك إضافة منطق للتحقق من صلاحيات المشرف
        # حالياً: السماح للجميع (يمكن تغييره لاحقاً)
        return True
    
    def show_help(self, channel_id):
        """عرض قائمة المساعدة"""
        embed = {
            "title": "🤖 **قائمة أوامر البوت** 🤖",
            "description": "الأوامر المتاحة:",
            "color": 3447003,
            "fields": [
                {"name": "!مساعدة", "value": "عرض هذه القائمة", "inline": False},
                {"name": "!قائمة_الرومات", "value": "عرض كل الرومات المعدة", "inline": False},
                {"name": "!إعدادات_الروم [اسم الروم]", "value": "عرض إعدادات روم معين", "inline": False},
                {"name": "!تعيين_محتوى", "value": "تعيين محتوى للروم الحالي (للمشرفين)", "inline": False},
                {"name": "!مسح_المحتوى", "value": "مسح محتوى الروم (للمشرفين)", "inline": False}
            ],
            "footer": {"text": "استخدم الأوامر بدون []"}
        }
        self.send_message(channel_id, "", embed)
    
    def show_channels_list(self, channel_id):
        """عرض قائمة الرومات المعدة"""
        channels = self.channel_content.get_all_channels()
        
        if not channels:
            self.send_message(channel_id, "❌ لا توجد رومات معدة حالياً")
            return
        
        embed = {
            "title": "📋 **قائمة الرومات المعدة** 📋",
            "description": f"عدد الرومات: {len(channels)}",
            "color": 3447003,
            "fields": []
        }
        
        for ch_id, ch_data in channels.items():
            content_type = ch_data.get('content_type', 'غير محدد')
            embed["fields"].append({
                "name": f"📁 {ch_data.get('name', 'غير معروف')}",
                "value": f"**النوع:** {content_type}\n**آخر تحديث:** {time.ctime(ch_data.get('updated_at', 0))}",
                "inline": False
            })
        
        self.send_message(channel_id, "", embed)
    
    def show_current_channel_settings(self, channel_id):
        """عرض إعدادات الروم الحالي"""
        channel_data = self.channel_content.get_channel_content(channel_id)
        
        if not channel_data:
            self.send_message(channel_id, "❌ هذا الروم ليس له إعدادات حالياً")
            return
        
        embed = self.create_content_embed(channel_data)
        embed["title"] = f"⚙️ **إعدادات الروم الحالي** ⚙️"
        embed["fields"].insert(0, {
            "name": "📊 معلومات الروم",
            "value": f"**النوع:** {channel_data.get('content_type', 'غير محدد')}\n**اسم الروم:** {channel_data.get('name', 'غير معروف')}",
            "inline": False
        })
        
        self.send_message(channel_id, "", embed)
    
    def show_channel_settings(self, channel_id, channel_name):
        """عرض إعدادات روم معين بالاسم"""
        channels = self.channel_content.get_all_channels()
        
        found_channel = None
        for ch_id, ch_data in channels.items():
            if ch_data.get('name', '').lower() == channel_name.lower():
                found_channel = (ch_id, ch_data)
                break
        
        if not found_channel:
            self.send_message(channel_id, f"❌ لم يتم العثور على روم باسم '{channel_name}'")
            return
        
        ch_id, ch_data = found_channel
        embed = self.create_content_embed(ch_data)
        embed["title"] = f"⚙️ **إعدادات روم {ch_data.get('name')}** ⚙️"
        embed["fields"].insert(0, {
            "name": "📊 معلومات الروم",
            "value": f"**النوع:** {ch_data.get('content_type', 'غير محدد')}\n**معرف الروم:** {ch_id}",
            "inline": False
        })
        
        self.send_message(channel_id, "", embed)
    
    def set_channel_content_command(self, channel_id, args):
        """تعيين محتوى للروم عبر الأمر"""
        if not args:
            self.send_message(channel_id, "❌ يرجى تحديد نوع المحتوى. الأنواع المتاحة: rules, welcome, announcement, text")
            return
        
        content_type = args.strip().lower()
        
        if content_type not in ['rules', 'welcome', 'announcement', 'text']:
            self.send_message(channel_id, "❌ نوع المحتوى غير صالح. الأنواع المتاحة: rules, welcome, announcement, text")
            return
        
        # الحصول على اسم الروم
        channels = self.get_guild_channels()
        channel_name = "غير معروف"
        for ch in channels:
            if ch.get('id') == channel_id:
                channel_name = ch.get('name', 'غير معروف')
                break
        
        # إنشاء محتوى افتراضي حسب النوع
        default_content = self.get_default_content(content_type)
        
        # حفظ الإعدادات
        self.channel_content.set_channel_content(channel_id, channel_name, content_type, default_content)
        
        self.send_message(channel_id, f"✅ تم تعيين محتوى نوع '{content_type}' لهذا الروم بنجاح!")
    
    def clear_channel_content_command(self, channel_id, args):
        """مسح محتوى الروم"""
        if args:
            # مسح روم معين بالاسم
            channels = self.channel_content.get_all_channels()
            for ch_id, ch_data in channels.items():
                if ch_data.get('name', '').lower() == args.strip().lower():
                    del self.channel_content.channels_data[ch_id]
                    self.channel_content.save_data()
                    self.send_message(channel_id, f"✅ تم مسح محتوى روم '{ch_data.get('name')}'")
                    return
            
            self.send_message(channel_id, f"❌ لم يتم العثور على روم باسم '{args.strip()}'")
        else:
            # مسح الروم الحالي
            if channel_id in self.channel_content.channels_data:
                channel_name = self.channel_content.channels_data[channel_id].get('name', 'غير معروف')
                del self.channel_content.channels_data[channel_id]
                self.channel_content.save_data()
                self.send_message(channel_id, f"✅ تم مسح محتوى الروم الحالي '{channel_name}'")
            else:
                self.send_message(channel_id, "❌ هذا الروم ليس له محتوى لمسحه")
    
    def get_default_content(self, content_type):
        """الحصول على محتوى افتراضي حسب النوع"""
        if content_type == 'rules':
            return {
                'title': '🎮 **قوانين السيرفر** 🎮',
                'description': 'يرجى الالتزام بالقوانين التالية:',
                'rules': DEFAULT_RULES,
                'color': 5814783,
                'image': 'https://i.imgur.com/3D-rules-example.png'
            }
        elif content_type == 'welcome':
            return {
                'title': '🎉 **أهلاً وسهلاً** 🎉',
                'description': 'أهلاً بك في سيرفرنا!',
                'messages': ['🎊 نتمنى لك وقتاً ممتعاً', '🌟 لا تتردد في المشاركة'],
                'color': 65280,
                'image': 'https://i.imgur.com/welcome-example.png'
            }
        elif content_type == 'announcement':
            return {
                'title': '📢 **إعلان هام** 📢',
                'description': 'إعلان مهم لجميع الأعضاء',
                'announcements': ['📌 تابع القوانين', '🎮 شارك في الأنشطة'],
                'color': 15158332,
                'image': 'https://i.imgur.com/announcement-example.png'
            }
        else:  # text
            return {
                'title': '📝 **رسالة** 📝',
                'description': 'محتوى نصي مخصص',
                'fields': [
                    {'name': 'مثال', 'value': 'هذا محتوى نصي مخصص', 'inline': False}
                ],
                'color': 3447003
            }
    
    def handle_voice_state_update(self, data):
        """معالجة تحديثات حالة الصوت"""
        user_id = data.get("user_id")
        channel_id = data.get("channel_id")
        member = data.get("member", {})
        user = member.get("user", {})
        user_name = user.get("username", "مستخدم")
        
        # إذا دخل المستخدم روم صوتي
        if channel_id and channel_id != self.last_voice_state.get(user_id):
            self.last_voice_state[user_id] = channel_id
            logger.info(f"🎤 المستخدم {user_name} دخل روم صوتي")
            
            # البحث عن روم نصي له إعدادات
            channels = self.get_guild_channels()
            
            for channel in channels:
                if channel.get("type") == 0:  # text channel
                    ch_id = channel.get("id")
                    channel_data = self.channel_content.get_channel_content(ch_id)
                    
                    if channel_data:
                        # إرسال المحتوى المخصص للروم
                        embed = self.create_content_embed(channel_data, user_name)
                        self.send_message(ch_id, "", embed)
                        logger.info(f"✅ تم إرسال محتوى مخصص لروم {channel.get('name')}")
                        break  # إرسال لروم واحد فقط
    
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
                "intents": (1 << 7) | (1 << 9),  # GUILD_VOICE_STATES | GUILD_MESSAGES
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
                    
                elif t == "MESSAGE_CREATE":
                    self.handle_message_create(d)
                    logger.debug(f"💬 رسالة جديدة تم استقبالها")
                    
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
        logger.info("🚀 بدء تشغيل بوت ديسكورد المتقدم...")
        
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
        
        logger.info("✅ البوت المتقدم يعمل الآن!")
        return True

# تشغيل البوت
if __name__ == "__main__":
    bot = DiscordBot()
    if bot.start():
        # تشغيل خادم Flask
        app.run(host='0.0.0.0', port=8080)
    else:
        logger.error("❌ فشل بدء البوت")
