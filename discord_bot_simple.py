import requests
import json
import os
import time
import threading
from flask import Flask, jsonify
import asyncio
import logging

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

class DiscordBot:
    def __init__(self):
        self.token = BOT_TOKEN
        self.application_id = APPLICATION_ID
        self.guild_id = GUILD_ID
        self.base_url = "https://discord.com/api/v10"
        self.headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json"
        }
        self.last_voice_state = {}
        self.running = True
        
    def send_message(self, channel_id, content, embed=None):
        """إرسال رسالة إلى قناة"""
        url = f"{self.base_url}/channels/{channel_id}/messages"
        data = {"content": content}
        
        if embed:
            data["embeds"] = [embed]
            
        try:
            response = requests.post(url, headers=self.headers, json=data)
            if response.status_code == 200:
                print(f"✅ تم إرسال الرسالة بنجاح")
                return True
            else:
                print(f"❌ خطأ في إرسال الرسالة: {response.status_code}")
                print(f"الرد: {response.text}")
                return False
        except Exception as e:
            print(f"❌ استثناء في إرسال الرسالة: {e}")
            return False
    
    def get_guild_channels(self):
        """الحصول على قنوات السيرفر"""
        url = f"{self.base_url}/guilds/{self.guild_id}/channels"
        try:
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ خطأ في جلب القنوات: {response.status_code}")
                return []
        except Exception as e:
            print(f"❌ استثناء في جلب القنوات: {e}")
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
            response = requests.get(url, headers=self.headers)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"❌ خطأ في جلب البوابة: {response.status_code}")
                return None
        except Exception as e:
            print(f"❌ استثناء في جلب البوابة: {e}")
            return None
    
    def handle_voice_state_update(self, data):
        """معالجة تحديثات حالة الصوت"""
        user_id = data.get("user_id")
        channel_id = data.get("channel_id")
        member = data.get("member", {})
        user_name = member.get("user", {}).get("username", "مستخدم")
        
        # إذا دخل المستخدم روم صوتي
        if channel_id:
            print(f"🎤 المستخدم {user_name} دخل روم صوتي")
            
            # الحصول على قنوات السيرفر
            channels = self.get_guild_channels()
            
            # البحث عن روم القوانين أو روم عام
            rules_channel = None
            for channel in channels:
                if channel.get("name") in ["قوانين", "rules", "general"]:
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
    
    def run_websocket(self):
        """تشغيل WebSocket للاستماع للأحداث"""
        import websocket
        import json
        
        gateway_info = self.get_gateway()
        if not gateway_info:
            print("❌ لا يمكن الاتصال بالبوابة")
            return
        
        ws_url = gateway_info.get("url")
        if not ws_url:
            print("❌ لم يتم العثور على رابط WebSocket")
            return
        
        def on_message(ws, message):
            try:
                data = json.loads(message)
                
                # التعامل مع أحداث البوابة
                op = data.get("op")
                t = data.get("t")
                d = data.get("d")
                
                if op == 10:  # Hello
                    heartbeat_interval = d.get("heartbeat_interval") / 1000
                    # إرسال heartbeat
                    threading.Timer(heartbeat_interval, lambda: ws.send(json.dumps({"op": 1, "d": None}))).start()
                    # إرسال identify
                    identify = {
                        "op": 2,
                        "d": {
                            "token": self.token,
                            "intents": 1 << 7,  # GUILD_VOICE_STATES
                            "properties": {
                                "$os": "linux",
                                "$browser": "my_library",
                                "$device": "my_library"
                            }
                        }
                    }
                    ws.send(json.dumps(identify))
                    print("✅ تم الاتصال بالبوابة بنجاح")
                
                elif t == "VOICE_STATE_UPDATE":
                    self.handle_voice_state_update(d)
                    print(f"📡 استقبلت حدث صوتي")
                
                elif op == 11:  # Heartbeat ACK
                    print("💓 Heartbeat received")
                    
            except Exception as e:
                print(f"❌ خطأ في معالجة الرسالة: {e}")
        
        def on_error(ws, error):
            print(f"❌ خطأ في WebSocket: {error}")
        
        def on_close(ws, close_status_code, close_msg):
            print("🔌 WebSocket مغلق")
            if self.running:
                print("🔄 إعادة المحاولة بعد 5 ثواني...")
                threading.Timer(5.0, self.run_websocket).start()
        
        def on_open(ws):
            print("🔗 WebSocket مفتوح")
        
        ws = websocket.WebSocketApp(
            ws_url,
            on_open=on_open,
            on_message=on_message,
            on_error=on_error,
            on_close=on_close
        )
        
        ws.run_forever()
    
    def start(self):
        """بدء البوت"""
        print("🚀 بدء تشغيل بوت ديسكورد...")
        
        if not self.token:
            print("❌ DISCORD_TOKEN غير موجود!")
            return
        
        if not self.guild_id:
            print("❌ GUILD_ID غير موجود!")
            return
        
        # بدء WebSocket في خيط منفصل
        ws_thread = threading.Thread(target=self.run_websocket)
        ws_thread.daemon = True
        ws_thread.start()
        
        print("✅ البوت يعمل الآن!")

# تشغيل البوت
if __name__ == "__main__":
    bot = DiscordBot()
    bot.start()
    
    # تشغيل خادم Flask
    app.run(host='0.0.0.0', port=8080)
