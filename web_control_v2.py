import requests
import json
import os
import time
import threading
from flask import Flask, jsonify, request, render_template_string, redirect, url_for, session, flash
import logging
import hashlib
import secrets
from datetime import datetime, timedelta
import base64
import io

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

# HTML Templates
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول -𝐋𝐄𝐆𝐀𝐂𝐘  لوحة تحكم البوت</title>
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
    </style>
</head>
<body>
    <div class="login-container">
        <h1>🤖𝐋𝐄𝐆𝐀𝐂𝐘  لوحة تحكم البوت</h1>
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
        <div class="bot-info"><p>لوحة تحكم بوت ديسكورد المتقدم</p></div>
    </div>
</body>
</html>
"""

class DiscordWebBot:
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
        self.servers_cache = {}
        self.channels_cache = {}
        self.last_cache_update = 0
        self.cache_duration = 300  # 5 دقائق
        
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
    
    def get_user_guilds(self):
        """الحصول على السيرفرات التي يوجد بها البوت"""
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
    
    def get_guild_channels(self, guild_id, force_refresh=False):
        """الحصول على قنوات سيرفر معين"""
        current_time = time.time()
        
        # التحقق من الـ cache
        if not force_refresh and guild_id in self.channels_cache:
            if (current_time - self.channels_cache[guild_id]['timestamp']) < self.cache_duration:
                return self.channels_cache[guild_id]['channels']
        
        url = f"{self.base_url}/guilds/{guild_id}/channels"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                channels = response.json()
                # تحديث الـ cache
                self.channels_cache[guild_id] = {
                    'channels': channels,
                    'timestamp': current_time
                }
                logger.info(f"✅ تم جلب {len(channels)} قناة من السيرفر {guild_id}")
                return channels
            else:
                logger.error(f"❌ خطأ في جلب القنوات: {response.status_code}")
                return self.channels_cache.get(guild_id, {}).get('channels', [])
        except Exception as e:
            logger.error(f"❌ استثناء في جلب القنوات: {e}")
            return self.channels_cache.get(guild_id, {}).get('channels', [])
    
    def get_guild_info(self, guild_id):
        """الحصول على معلومات سيرفر معين"""
        url = f"{self.base_url}/guilds/{guild_id}"
        try:
            response = requests.get(url, headers=self.headers, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"❌ خطأ في جلب معلومات السيرفر: {response.status_code}")
                return {}
        except Exception as e:
            logger.error(f"❌ استثناء في جلب معلومات السيرفر: {e}")
            return {}
    
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
                return True, response.json()
            else:
                logger.error(f"❌ خطأ في إرسال الرسالة: {response.status_code}")
                logger.error(f"الرد: {response.text}")
                return False, response.text
        except Exception as e:
            logger.error(f"❌ استثناء في إرسال الرسالة: {e}")
            return False, str(e)
    
    def upload_image_to_discord(self, channel_id, image_data, filename="image.png"):
        """رفع صورة إلى ديسكورد"""
        url = f"{self.base_url}/channels/{channel_id}/messages"
        
        files = {
            'file': (filename, image_data, 'image/png')
        }
        
        try:
            response = requests.post(url, headers={"Authorization": f"Bot {self.token}"}, files=files, timeout=30)
            if response.status_code == 200:
                result = response.json()
                # الحصول على رابط الصورة من الرسالة
                attachments = result.get('attachments', [])
                if attachments:
                    image_url = attachments[0].get('url')
                    logger.info(f"✅ تم رفع الصورة بنجاح")
                    return True, image_url
            else:
                logger.error(f"❌ خطأ في رفع الصورة: {response.status_code}")
                return False, None
        except Exception as e:
            logger.error(f"❌ استثناء في رفع الصورة: {e}")
            return False, None
    
    def create_embed(self, title=None, description=None, color="#5865F2", image_url=None):
        """إنشاء رسالة مضمنة"""
        embed = {
            "color": int(color.replace("#", ""), 16),
            "type": "rich"
        }
        
        if title:
            embed["title"] = title
        if description:
            embed["description"] = description
        if image_url:
            embed["image"] = {"url": image_url}
            
        return embed

# إنشاء كائن البوت
discord_bot = DiscordWebBot()

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
        
        # التحقق من كلمة المرور
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
    guilds = discord_bot.get_user_guilds()
    
    # حساب الإحصائيات
    total_servers = len(guilds)
    total_channels = 0
    text_channels = 0
    voice_channels = 0
    total_members = 0
    
    for guild in guilds:
        guild_info = discord_bot.get_guild_info(guild['id'])
        if guild_info:
            total_members += guild_info.get('member_count', 0)
            channels = discord_bot.get_guild_channels(guild['id'])
            total_channels += len(channels)
            text_channels += len([ch for ch in channels if ch.get('type') == 0])
            voice_channels += len([ch for ch in channels if ch.get('type') == 2])
    
    stats = {
        'total_servers': total_servers,
        'total_channels': total_channels,
        'text_channels': text_channels,
        'voice_channels': voice_channels,
        'total_members': total_members
    }
    
    return render_template_string(DASHBOARD_TEMPLATE, stats=stats)

@app.route('/api/servers')
def api_servers():
    """API للحصول على السيرفرات"""
    if 'logged_in' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    
    guilds = discord_bot.get_user_guilds()
    return jsonify(guilds)

@app.route('/api/servers/<server_id>/channels')
def api_server_channels(server_id):
    """API للحصول على قنوات سيرفر معين"""
    if 'logged_in' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    
    channels = discord_bot.get_guild_channels(server_id)
    return jsonify(channels)

@app.route('/api/send-message', methods=['POST'])
def api_send_message():
    """API لإرسال الرسائل"""
    if 'logged_in' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    
    try:
        # معالجة رفع الصور
        image_url = request.form.get('image_url', '')
        image_file = request.files.get('image_file')
        
        if image_file:
            # رفع الصورة إلى ديسكورد أولاً
            channel_id = request.form.get('channel_id')
            success, uploaded_url = discord_bot.upload_image_to_discord(
                channel_id, 
                image_file.read(),
                image_file.filename
            )
            if success:
                image_url = uploaded_url
            else:
                return jsonify({'success': False, 'error': 'فشل في رفع الصورة'})
        
        channel_id = request.form.get('channel_id')
        message = request.form.get('message', '')
        embed_title = request.form.get('embed_title', '')
        embed_color = request.form.get('embed_color', '#5865F2')
        
        if not channel_id:
            return jsonify({'success': False, 'error': 'لم يتم تحديد القناة'})
        
        # إنشاء embed إذا كان هناك عنوان أو صورة
        embed = None
        if embed_title or image_url:
            embed = discord_bot.create_embed(
                title=embed_title,
                description=message if not embed_title else None,
                color=embed_color,
                image_url=image_url
            )
        
        # إرسال الرسالة
        success, result = discord_bot.send_message(
            channel_id,
            message if not embed else '',
            embed=embed
        )
        
        if success:
            return jsonify({'success': True, 'message_id': result.get('id')})
        else:
            return jsonify({'success': False, 'error': str(result)})
            
    except Exception as e:
        logger.error(f"Error in send_message API: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": time.time()})

@app.route('/test')
def test():
    return jsonify({
        "token_exists": bool(BOT_TOKEN),
        "app_id_exists": bool(APPLICATION_ID),
        "guild_id_exists": bool(GUILD_ID),
        "token_length": len(BOT_TOKEN) if BOT_TOKEN else 0,
        "bot_connected": discord_bot.test_connection()[0]
    })

if __name__ == "__main__":
    # اختبار الاتصال
    connected, bot_info = discord_bot.test_connection()
    if connected:
        logger.info("✅ البوت متصل وجاهز للعمل")
        app.run(host='0.0.0.0', port=8080, debug=False)
    else:
        logger.error("❌ فشل الاتصال بالبوت")
        app.run(host='0.0.0.0', port=8080, debug=False)
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>𝐋𝐄𝐆𝐀𝐂𝐘 لوحة تحكم البوت المتقدم</title>
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
        .main-content {
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 30px;
        }
        .card {
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.08);
            overflow: hidden;
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
        select, textarea, input[type="text"], input[type="url"] {
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
        }
        .btn:hover { transform: translateY(-2px); }
        .message-preview {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            margin-top: 15px;
        }
        .preview-title { font-weight: 600; color: #495057; margin-bottom: 10px; }
        
        /* Color Picker Advanced */
        .color-picker-container {
            background: white;
            border: 2px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 20px;
        }
        .color-display {
            width: 100%;
            height: 60px;
            border-radius: 8px;
            margin-bottom: 15px;
            border: 2px solid #ddd;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
            color: white;
            text-shadow: 0 1px 3px rgba(0,0,0,0.5);
        }
        .color-inputs {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
            margin-bottom: 15px;
        }
        .color-input-group {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        .color-input-group label {
            width: 60px;
            margin-bottom: 0;
            font-size: 12px;
        }
        .color-input-group input {
            flex: 1;
            padding: 8px;
            border: 1px solid #ddd;
            border-radius: 4px;
            font-size: 14px;
        }
        .color-slider {
            width: 100%;
            margin-bottom: 10px;
        }
        .color-slider input[type="range"] {
            width: 100%;
            cursor: pointer;
        }
        .opacity-slider {
            margin-top: 10px;
        }
        
        /* File Upload */
        .file-upload {
            border: 2px dashed #667eea;
            border-radius: 8px;
            padding: 30px;
            text-align: center;
            cursor: pointer;
            transition: all 0.3s;
        }
        .file-upload:hover {
            background: #f8f9fa;
            border-color: #764ba2;
        }
        .file-upload input {
            display: none;
        }
        .file-upload i {
            font-size: 48px;
            color: #667eea;
            margin-bottom: 10px;
        }
        .file-upload p {
            color: #666;
            margin-bottom: 10px;
        }
        .file-preview {
            margin-top: 15px;
            max-width: 100%;
            border-radius: 8px;
            display: none;
        }
        .file-preview img {
            max-width: 100%;
            border-radius: 8px;
        }
        
        /* Server and Channel Selection */
        .server-channel-container {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 15px;
            margin-bottom: 20px;
        }
        .servers-list, .channels-list {
            max-height: 200px;
            overflow-y: auto;
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 10px;
        }
        .server-item, .channel-item {
            padding: 10px;
            margin-bottom: 5px;
            background: #f8f9fa;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.2s;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .server-item:hover, .channel-item:hover { background: #e9ecef; }
        .server-item.selected, .channel-item.selected {
            background: #667eea;
            color: white;
        }
        .server-icon {
            width: 40px;
            height: 40px;
            border-radius: 50%;
            background: #667eea;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
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
        .loading {
            display: none;
            text-align: center;
            padding: 20px;
        }
        .spinner {
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            width: 40px;
            height: 40px;
            animation: spin 1s linear infinite;
            margin: 0 auto;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        @media (max-width: 1024px) {
            .main-content { grid-template-columns: 1fr; }
            .server-channel-container { grid-template-columns: 1fr; }
        }
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1>🤖𝐋𝐄𝐆𝐀𝐂𝐘  لوحة تحكم البوت المتقدم</h1>
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
                <div class="stat-number">{{ stats.text_channels }}</div>
                <div class="stat-label">القنوات النصية</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.voice_channels }}</div>
                <div class="stat-label">القنوات الصوتية</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_members }}</div>
                <div class="stat-label">الأعضاء</div>
            </div>
        </div>
        
        <div class="main-content">
            <div class="card">
                <div class="card-header">
                    <i class="fas fa-paper-plane"></i>
                    إرسال رسالة
                </div>
                <div class="card-body">
                    <form id="messageForm">
                        <div class="server-channel-container">
                            <div>
                                <label>اختر السيرفر:</label>
                                <div class="servers-list" id="serversList">
                                    <div class="loading">
                                        <div class="spinner"></div>
                                        <p>جاري تحميل السيرفرات...</p>
                                    </div>
                                </div>
                                <input type="hidden" id="selectedServer" name="server" required>
                            </div>
                            <div>
                                <label>اختر القناة:</label>
                                <div class="channels-list" id="channelsList">
                                    <p style="color: #999; text-align: center;">اختر سيرفر أولاً</p>
                                </div>
                                <input type="hidden" id="selectedChannel" name="channel" required>
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="message">الرسالة:</label>
                            <textarea id="message" name="message" placeholder="اكتب رسالتك هنا..."></textarea>
                        </div>
                        
                        <div class="form-group">
                            <label>رفع صورة من الجهاز:</label>
                            <div class="file-upload" id="fileUpload">
                                <i class="fas fa-cloud-upload-alt"></i>
                                <p>اضغط هنا لرفع صورة أو اسحبها هنا</p>
                                <input type="file" id="imageFile" accept="image/*">
                            </div>
                            <div class="file-preview" id="filePreview">
                                <img id="previewImage" src="" alt="معاينة الصورة">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="imageUrl">أو رابط صورة (اختياري):</label>
                            <input type="url" id="imageUrl" name="imageUrl" placeholder="https://example.com/image.png">
                        </div>
                        
                        <div class="color-picker-container">
                            <label>اختيار اللون المتقدم:</label>
                            <div class="color-display" id="colorDisplay">#5865F2</div>
                            
                            <div class="color-inputs">
                                <div class="color-input-group">
                                    <label>Hex:</label>
                                    <input type="text" id="hexInput" value="#5865F2" maxlength="7">
                                </div>
                                <div class="color-input-group">
                                    <label>RGB:</label>
                                    <input type="text" id="rgbInput" value="88, 101, 242" readonly>
                                </div>
                            </div>
                            
                            <div class="color-slider">
                                <label>الأحمر (R):</label>
                                <input type="range" id="redSlider" min="0" max="255" value="88">
                            </div>
                            <div class="color-slider">
                                <label>الأخضر (G):</label>
                                <input type="range" id="greenSlider" min="0" max="255" value="101">
                            </div>
                            <div class="color-slider">
                                <label>الأزرق (B):</label>
                                <input type="range" id="blueSlider" min="0" max="255" value="242">
                            </div>
                            <div class="color-slider opacity-slider">
                                <label>الشفافية (Opacity):</label>
                                <input type="range" id="opacitySlider" min="0" max="100" value="100">
                            </div>
                        </div>
                        
                        <div class="form-group">
                            <label for="embedTitle">عنوان الرسالة المضمنة (اختياري):</label>
                            <input type="text" id="embedTitle" name="embedTitle" placeholder="عنوان الرسالة">
                        </div>
                        
                        <button type="submit" class="btn">إرسال الرسالة</button>
                    </form>
                    
                    <div class="message-preview" id="messagePreview" style="display: none;">
                        <div class="preview-title">معاينة الرسالة:</div>
                        <div id="previewContent"></div>
                    </div>
                </div>
            </div>
            
            <div class="card">
                <div class="card-header">
                    <i class="fas fa-history"></i>
                    الرسائل المرسلة
                </div>
                <div class="card-body">
                    <div id="messagesList">
                        <p>لم يتم إرسال رسائل بعد</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let selectedServerId = null;
        let selectedChannelId = null;
        let servers = [];
        let channels = {};
        let uploadedImageData = null;
        
        // تحميل السيرفرات
        function loadServers() {
            fetch('/api/servers')
                .then(response => response.json())
                .then(data => {
                    servers = data;
                    displayServers(data);
                })
                .catch(error => {
                    console.error('Error loading servers:', error);
                    document.getElementById('serversList').innerHTML = '<p style="color: red;">خطأ في تحميل السيرفرات</p>';
                });
        }
        
        // عرض السيرفرات
        function displayServers(serversData) {
            const container = document.getElementById('serversList');
            
            if (serversData.length === 0) {
                container.innerHTML = '<p>لا توجد سيرفرات</p>';
                return;
            }
            
            container.innerHTML = serversData.map(server => `
                <div class="server-item" data-id="${server.id}" data-name="${server.name}">
                    <div class="server-icon">${server.name.charAt(0).toUpperCase()}</div>
                    <span>${server.name}</span>
                </div>
            `).join('');
            
            // إضافة حدث النقر
            container.querySelectorAll('.server-item').forEach(item => {
                item.addEventListener('click', function() {
                    container.querySelectorAll('.server-item').forEach(i => i.classList.remove('selected'));
                    this.classList.add('selected');
                    selectedServerId = this.dataset.id;
                    document.getElementById('selectedServer').value = selectedServerId;
                    loadChannels(selectedServerId);
                });
            });
        }
        
        // تحميل قنوات سيرفر معين
        function loadChannels(serverId) {
            document.getElementById('channelsList').innerHTML = '<div class="loading"><div class="spinner"></div><p>جاري تحميل القنوات...</p></div>';
            
            fetch(`/api/servers/${serverId}/channels`)
                .then(response => response.json())
                .then(data => {
                    channels[serverId] = data;
                    displayChannels(data);
                })
                .catch(error => {
                    console.error('Error loading channels:', error);
                    document.getElementById('channelsList').innerHTML = '<p style="color: red;">خطأ في تحميل القنوات</p>';
                });
        }
        
        // عرض القنوات
        function displayChannels(channelsData) {
            const container = document.getElementById('channelsList');
            const textChannels = channelsData.filter(ch => ch.type === 0);
            
            if (textChannels.length === 0) {
                container.innerHTML = '<p>لا توجد قنوات نصية</p>';
                return;
            }
            
            container.innerHTML = textChannels.map(channel => `
                <div class="channel-item" data-id="${channel.id}" data-name="${channel.name}">
                    <i class="fas fa-hashtag"></i>
                    <span>${channel.name}</span>
                </div>
            `).join('');
            
            // إضافة حدث النقر
            container.querySelectorAll('.channel-item').forEach(item => {
                item.addEventListener('click', function() {
                    container.querySelectorAll('.channel-item').forEach(i => i.classList.remove('selected'));
                    this.classList.add('selected');
                    selectedChannelId = this.dataset.id;
                    document.getElementById('selectedChannel').value = selectedChannelId;
                });
            });
        }
        
        // Color Picker Logic
        function updateColor() {
            const r = parseInt(document.getElementById('redSlider').value);
            const g = parseInt(document.getElementById('greenSlider').value);
            const b = parseInt(document.getElementById('blueSlider').value);
            const opacity = parseInt(document.getElementById('opacitySlider').value) / 100;
            
            const hex = '#' + [r, g, b].map(x => {
                const hex = x.toString(16);
                return hex.length === 1 ? '0' + hex : hex;
            }).join('');
            
            document.getElementById('colorDisplay').style.backgroundColor = hex;
            document.getElementById('colorDisplay').style.opacity = opacity;
            document.getElementById('colorDisplay').textContent = hex;
            document.getElementById('hexInput').value = hex;
            document.getElementById('rgbInput').value = `${r}, ${g}, ${b}`;
            
            updatePreview();
        }
        
        // File Upload Logic
        document.getElementById('fileUpload').addEventListener('click', function() {
            document.getElementById('imageFile').click();
        });
        
        document.getElementById('imageFile').addEventListener('change', function(e) {
            const file = e.target.files[0];
            if (file) {
                const reader = new FileReader();
                reader.onload = function(event) {
                    uploadedImageData = event.target.result;
                    document.getElementById('previewImage').src = uploadedImageData;
                    document.getElementById('filePreview').style.display = 'block';
                    updatePreview();
                };
                reader.readAsDataURL(file);
            }
        });
        
        // Preview Update
        function updatePreview() {
            const message = document.getElementById('message').value;
            const imageUrl = document.getElementById('imageUrl').value;
            const embedTitle = document.getElementById('embedTitle').value;
            const color = document.getElementById('hexInput').value;
            const opacity = document.getElementById('opacitySlider').value / 100;
            
            if (!message && !imageUrl && !embedTitle && !uploadedImageData) {
                document.getElementById('messagePreview').style.display = 'none';
                return;
            }
            
            let previewHTML = '';
            
            if (embedTitle) {
                previewHTML += `<div style="background: ${color}; color: white; padding: 10px; border-radius: 5px; margin-bottom: 10px; font-weight: bold; opacity: ${opacity};">${embedTitle}</div>`;
            }
            
            if (message) {
                previewHTML += `<div style="margin-bottom: 10px;">${message}</div>`;
            }
            
            const imageToShow = uploadedImageData || imageUrl;
            if (imageToShow) {
                previewHTML += `<img src="${imageToShow}" style="max-width: 100%; border-radius: 5px;" onerror="this.style.display='none'">`;
            }
            
            document.getElementById('previewContent').innerHTML = previewHTML;
            document.getElementById('messagePreview').style.display = 'block';
        }
        
        // Send Message
        document.getElementById('messageForm').addEventListener('submit', function(e) {
            e.preventDefault();
            
            if (!selectedServerId) {
                alert('يرجى اختيار سيرفر أولاً');
                return;
            }
            
            if (!selectedChannelId) {
                alert('يرجى اختيار قناة أولاً');
                return;
            }
            
            const formData = new FormData();
            formData.append('channel_id', selectedChannelId);
            formData.append('message', document.getElementById('message').value);
            formData.append('image_url', document.getElementById('imageUrl').value);
            formData.append('embed_title', document.getElementById('embedTitle').value);
            formData.append('embed_color', document.getElementById('hexInput').value);
            
            if (uploadedImageData && document.getElementById('imageFile').files[0]) {
                formData.append('image_file', document.getElementById('imageFile').files[0]);
            }
            
            fetch('/api/send-message', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(result => {
                if (result.success) {
                    alert('تم إرسال الرسالة بنجاح!');
                    this.reset();
                    document.getElementById('messagePreview').style.display = 'none';
                    document.getElementById('filePreview').style.display = 'none';
                    uploadedImageData = null;
                    addToMessagesList({
                        message: formData.get('message'),
                        embed_title: formData.get('embed_title'),
                        image_url: formData.get('image_url') || uploadedImageData
                    });
                } else {
                    alert('خطأ: ' + result.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('حدث خطأ أثناء إرسال الرسالة');
            });
        });
        
        // Add to Messages List
        function addToMessagesList(messageData) {
            const messagesList = document.getElementById('messagesList');
            const timestamp = new Date().toLocaleString('ar-EG');
            
            const messageItem = document.createElement('div');
            messageItem.style.cssText = 'background: #f8f9fa; padding: 15px; border-radius: 8px; margin-bottom: 10px;';
            messageItem.innerHTML = `
                <div style="font-weight: bold; color: #667eea;">${messageData.embed_title || 'رسالة جديدة'}</div>
                <div style="color: #666; font-size: 12px; margin-bottom: 5px;">${timestamp}</div>
                <div>${messageData.message || ''}</div>
                ${messageData.image_url ? `<img src="${messageData.image_url}" style="max-width: 100px; margin-top: 5px; border-radius: 4px;">` : ''}
            `;
            
            if (messagesList.children[0].textContent === 'لم يتم إرسال رسائل بعد') {
                messagesList.innerHTML = '';
            }
            
            messagesList.insertBefore(messageItem, messagesList.firstChild);
        }
        
        // Event Listeners
        ['redSlider', 'greenSlider', 'blueSlider', 'opacitySlider'].forEach(id => {
            document.getElementById(id).addEventListener('input', updateColor);
        });
        
        ['message', 'imageUrl', 'embedTitle'].forEach(id => {
            document.getElementById(id).addEventListener('input', updatePreview);
        });
        
        // Load servers on page load
        loadServers();
    </script>
</body>
</html>
"""
