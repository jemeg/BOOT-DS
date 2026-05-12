import requests
import json
import os
import time
from flask import Flask, jsonify, request, render_template_string, redirect, url_for, session, flash
import logging
import hashlib
import secrets

# إعداد الـ logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# إعدادات البوت
BOT_TOKEN = os.getenv('DISCORD_TOKEN')
ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin123')

# إعدادات Flask
app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET', secrets.token_hex(32))

# القوانين الافتراضية
DEFAULT_RULES = [
    "🚫 ممنوع السب والشتم",
    "🚫 ممنوع نشر الروابط بدون إذن",
    "🚫 ممنوع إزعاج الأعضاء",
    "🚫 ممنوع نشر محتوى غير لائق",
    "📝 احترام الجميع مطلوب",
    "🎮 الالتزام بقوانين اللعب"
]

class RulesManager:
    def __init__(self):
        self.rules_file = 'simple_rules.json'
        self.data = self.load_data()
        
    def load_data(self):
        """تحميل بيانات القوانين"""
        try:
            if os.path.exists(self.rules_file):
                with open(self.rules_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {'rules': DEFAULT_RULES}
        except Exception as e:
            logger.error(f"Error loading rules data: {e}")
            return {'rules': DEFAULT_RULES}
    
    def save_data(self):
        """حفظ بيانات القوانين"""
        try:
            with open(self.rules_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving rules data: {e}")
            return False
    
    def get_rules_embed(self, member_name=None):
        """إنشاء رسالة القوانين"""
        rules_text = '\n'.join([f"**{i+1}.** {rule}" for i, rule in enumerate(self.data['rules'])])
        
        embed = {
            "title": "📜 قوانين السيرفر",
            "description": f"مرحباً بك في السيرفر! يرجى قراءة القوانين أدناه:\n\n{rules_text}",
            "color": 0x667eea,
            "footer": {"text": f"مرحباً {member_name or 'بك'}!"}
        }
        
        return embed

class DiscordBot:
    def __init__(self):
        self.token = BOT_TOKEN
        self.base_url = "https://discord.com/api/v10"
        self.headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (Render, 1.0)"
        }
        self.rules_manager = RulesManager()
        
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
    
    def send_rules_message(self, channel_id, member_name):
        """إرسال رسالة القوانين"""
        embed = self.rules_manager.get_rules_embed(member_name)
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

# إنشاء كائن البوت
discord_bot = DiscordBot()
rules_manager = discord_bot.rules_manager

# HTML Templates
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول - لوحة تحكم القوانين</title>
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
        <h1>📜 لوحة تحكم القوانين</h1>
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
        <div class="bot-info"><p>لوحة تحكم بوت القوانين البسيط</p></div>
    </div>
</body>
</html>
"""

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم القوانين</title>
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
            max-width: 1200px;
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
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
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
        select, textarea, input[type="text"] {
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
        .btn-danger {
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        }
        .rules-list {
            display: grid;
            gap: 15px;
        }
        .rule-item {
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 8px;
            padding: 15px;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        .rule-number {
            width: 40px;
            height: 40px;
            background: #667eea;
            color: white;
            border-radius: 50%;
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: bold;
        }
        .rule-text {
            flex: 1;
            font-size: 16px;
        }
        .rule-actions {
            display: flex;
            gap: 10px;
        }
        .icon-btn {
            width: 35px;
            height: 35px;
            border: none;
            border-radius: 50%;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            transition: all 0.3s;
        }
        .icon-btn.delete {
            background: #e74c3c;
            color: white;
        }
        .icon-btn:hover {
            transform: scale(1.1);
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
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1>📜 لوحة تحكم القوانين</h1>
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
                <div class="stat-number">{{ stats.rules_count }}</div>
                <div class="stat-label">القوانين</div>
            </div>
        </div>
        
        <div class="card">
            <div class="card-header">
                <i class="fas fa-gavel"></i>
                إدارة القوانين
            </div>
            <div class="card-body">
                <div class="form-group">
                    <label>إرسال رسالة القوانين:</label>
                    <div style="display: grid; grid-template-columns: 2fr 1fr; gap: 10px;">
                        <select id="serverSelect" onchange="loadChannels()">
                            <option value="">اختر السيرفر...</option>
                            {% for server in servers %}
                            <option value="{{ server.id }}">{{ server.name }}</option>
                            {% endfor %}
                        </select>
                        <select id="channelSelect" disabled>
                            <option value="">اختر القناة...</option>
                        </select>
                    </div>
                </div>
                
                <div class="form-group">
                    <label>اسم المستخدم (اختياري):</label>
                    <input type="text" id="memberName" placeholder="اكتب اسم المستخدم...">
                </div>
                
                <button class="btn" onclick="sendRules()">
                    <i class="fas fa-paper-plane"></i> إرسال القوانين
                </button>
                
                <div style="margin-top: 30px;">
                    <h3 style="margin-bottom: 15px;">القوانين الحالية:</h3>
                    <div class="rules-list" id="rulesList">
                        {% for rule in rules %}
                        <div class="rule-item">
                            <div class="rule-number">{{ loop.index }}</div>
                            <div class="rule-text">{{ rule }}</div>
                            <button class="icon-btn delete" onclick="deleteRule({{ loop.index0 }})">
                                <i class="fas fa-trash"></i>
                            </button>
                        </div>
                        {% endfor %}
                    </div>
                </div>
                
                <div class="form-group" style="margin-top: 20px;">
                    <label>إضافة قانون جديد:</label>
                    <div style="display: flex; gap: 10px;">
                        <input type="text" id="newRule" placeholder="اكتب القانون الجديد..." style="flex: 1;">
                        <button class="btn" onclick="addRule()">
                            <i class="fas fa-plus"></i> إضافة
                        </button>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        let servers = {{ servers|tojson }};
        let channels = {};
        
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
        
        function sendRules() {
            const channelId = document.getElementById('channelSelect').value;
            const memberName = document.getElementById('memberName').value;
            
            if (!channelId) {
                alert('يرجى اختيار القناة أولاً');
                return;
            }
            
            fetch('/api/send-rules', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    channel_id: channelId,
                    member_name: memberName
                })
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
        
        function addRule() {
            const ruleText = document.getElementById('newRule').value.trim();
            
            if (!ruleText) {
                alert('يرجى كتابة القانون');
                return;
            }
            
            fetch('/api/rules', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'add',
                    rule: ruleText
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('newRule').value = '';
                    location.reload();
                } else {
                    alert('خطأ: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('حدث خطأ أثناء إضافة القانون');
            });
        }
        
        function deleteRule(index) {
            if (confirm('هل أنت متأكد من حذف هذا القانون؟')) {
                fetch('/api/rules', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        action: 'delete',
                        index: index
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        location.reload();
                    } else {
                        alert('خطأ: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('حدث خطأ أثناء حذف القانون');
                });
            }
        }
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
    guilds = discord_bot.get_user_guilds()
    
    # حساب الإحصائيات
    total_servers = len(guilds)
    total_channels = 0
    for guild in guilds:
        channels = discord_bot.get_guild_channels(guild['id'])
        total_channels += len(channels)
    
    stats = {
        'total_servers': total_servers,
        'total_channels': total_channels,
        'rules_count': len(rules_manager.data['rules'])
    }
    
    return render_template_string(DASHBOARD_TEMPLATE, 
                              servers=guilds, 
                              stats=stats, 
                              rules=rules_manager.data['rules'])

@app.route('/api/servers/<server_id>/channels')
def api_server_channels(server_id):
    if 'logged_in' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    channels = discord_bot.get_guild_channels(server_id)
    return jsonify(channels)

@app.route('/api/send-rules', methods=['POST'])
def api_send_rules():
    if 'logged_in' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    
    try:
        data = request.get_json()
        channel_id = data.get('channel_id')
        member_name = data.get('member_name', '')
        
        if not channel_id:
            return jsonify({'success': False, 'error': 'لم يتم تحديد القناة'})
        
        success, result = discord_bot.send_rules_message(channel_id, member_name)
        
        if success:
            return jsonify({'success': True, 'message_id': result.get('id')})
        else:
            return jsonify({'success': False, 'error': str(result)})
    except Exception as e:
        logger.error(f"Error in send_rules API: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/rules', methods=['GET', 'POST'])
def api_rules():
    if 'logged_in' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    
    if request.method == 'GET':
        return jsonify({'rules': rules_manager.data['rules']})
    
    if request.method == 'POST':
        data = request.get_json()
        action = data.get('action')
        
        if action == 'add':
            rule_text = data.get('rule', '').strip()
            if rule_text:
                rules_manager.data['rules'].append(rule_text)
                if rules_manager.save_data():
                    return jsonify({'success': True})
                else:
                    return jsonify({'success': False, 'error': 'فشل في حفظ القانون'})
        
        elif action == 'delete':
            index = data.get('index')
            if 0 <= index < len(rules_manager.data['rules']):
                del rules_manager.data['rules'][index]
                if rules_manager.save_data():
                    return jsonify({'success': True})
                else:
                    return jsonify({'success': False, 'error': 'فشل في حذف القانون'})
        
        return jsonify({'success': False, 'error': 'إجراء غير صالح'})

@app.route('/health')
def health():
    return jsonify({"status": "healthy", "timestamp": time.time()})

@app.route('/test')
def test():
    return jsonify({
        "token_exists": bool(BOT_TOKEN),
        "token_length": len(BOT_TOKEN) if BOT_TOKEN else 0,
        "bot_connected": discord_bot.test_connection()[0],
        "rules_count": len(rules_manager.data['rules'])
    })

if __name__ == "__main__":
    # اختبار الاتصال
    connected, bot_info = discord_bot.test_connection()
    if connected:
        logger.info("✅ بوت القوانين البسيط متصل وجاهز للعمل")
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 3000)), debug=False)
    else:
        logger.error("❌ فشل الاتصال بالبوت")
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 3000)), debug=False)
