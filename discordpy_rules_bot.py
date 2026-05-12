import discord
from discord.ext import commands
import json
import os
import logging
import hashlib
import secrets
from flask import Flask, jsonify, request, render_template_string, redirect, url_for, session, flash
from threading import Thread
import asyncio

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

# ملف حفظ القوانين
RULES_FILE = "rules_data.json"

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

def load_rules():
    """تحميل القوانين من الملف"""
    try:
        if os.path.exists(RULES_FILE):
            with open(RULES_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        else:
            # إنشاء الملف بالقوانين الافتراضية
            save_rules(DEFAULT_RULES)
            return DEFAULT_RULES.copy()
    except Exception as e:
        logger.error(f"❌ خطأ في تحميل القوانين: {e}")
        return DEFAULT_RULES.copy()

def save_rules(rules):
    """حفظ القوانين في الملف"""
    try:
        with open(RULES_FILE, 'w', encoding='utf-8') as f:
            json.dump(rules, f, ensure_ascii=False, indent=2)
        logger.info("✅ تم حفظ القوانين بنجاح")
        return True
    except Exception as e:
        logger.error(f"❌ خطأ في حفظ القوانين: {e}")
        return False

# تحميل القوانين عند بدء التشغيل
CURRENT_RULES = load_rules()

# إعدادات intents
intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
intents.voice_states = True

# إنشاء البوت
bot = commands.Bot(command_prefix='!', intents=intents)

class RulesView(discord.ui.View):
    """عرض القوانين التفاعلية"""
    def __init__(self, rules):
        super().__init__(timeout=None)
        self.rules = rules
        
        # إضافة أزرار لكل فئة
        for category in rules.keys():
            button = discord.ui.Button(
                label=category,
                style=discord.ButtonStyle.primary,
                custom_id=f"rules_{category}"
            )
            button.callback = self.create_callback(category)
            self.add_item(button)
    
    def create_callback(self, category):
        """إنشاء callback لكل زر"""
        async def callback(interaction):
            rules = load_rules().get(category, [])
            if not rules:
                await interaction.response.send_message("❌ فئة غير موجودة", ephemeral=True)
                return
            
            rules_text = '\n'.join([f"**{i+1}.** {rule}" for i, rule in enumerate(rules)])
            
            embed = discord.Embed(
                title=f"📜 {category}",
                description=f"قوانين {category}:\n\n{rules_text}",
                color=0x667eea
            )
            embed.set_footer(text=f"مرحباً {interaction.user.name}!")
            
            await interaction.response.send_message(embed=embed, ephemeral=True)
        
        return callback

@bot.event
async def on_ready():
    """عند جاهزية البوت"""
    logger.info(f"✅ البوت جاهز! {bot.user.name}#{bot.user.discriminator}")
    logger.info(f"📊 السيرفرات: {len(bot.guilds)}")

@bot.event
async def on_voice_state_update(member, before, after):
    """معالجة دخول/خروج القنوات الصوتية"""
    if after.channel and not before.channel:
        # المستخدم دخل قناة صوتية
        rules = load_rules()
        view = RulesView(rules)
        
        embed = discord.Embed(
            title="📜 اختر فئة القوانين",
            description=f"مرحباً بك {member.name}! 🎊\n\nاختر فئة القوانين التي تريد مشاهدتها:",
            color=0x667eea
        )
        embed.set_footer(text=f"مرحباً {member.name}!")
        
        try:
            await after.channel.send(embed=embed, view=view)
            logger.info(f"📜 تم إرسال القوانين للمستخدم {member.name}")
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال القوانين: {e}")

# HTML Templates
LOGIN_TEMPLATE = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>تسجيل الدخول - لوحة تحكم القوانين التفاعلية</title>
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
        <h1>📜 لوحة تحكم القوانين التفاعلية</h1>
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
        <div class="bot-info"><p>لوحة تحكم بوت القوانين التفاعلي</p></div>
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

INTERACTIVE_DASHBOARD = """
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>لوحة تحكم القوانين التفاعلية</title>
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
        select, textarea, input[type="text"], input[type="file"] {
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
        .bot-status {
            background: #28a745;
            color: white;
            padding: 10px;
            border-radius: 6px;
            text-align: center;
            margin-bottom: 20px;
        }
        .bot-status.disconnected {
            background: #dc3545;
        }
        .image-preview {
            max-width: 200px;
            max-height: 200px;
            margin: 10px auto;
            border-radius: 8px;
            border: 2px solid #ddd;
            display: block;
        }
        .feature-highlight {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            padding: 15px;
            border-radius: 8px;
            margin-bottom: 20px;
            text-align: center;
        }
        .feature-highlight h3 {
            margin-bottom: 10px;
        }
        .two-column {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 20px;
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
    </style>
</head>
<body>
    <div class="header">
        <div class="header-content">
            <h1>📜 لوحة تحكم القوانين التفاعلية</h1>
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
        
        <div class="feature-highlight">
            <h3>🎯 نظام القوانين التفاعلي</h3>
            <p>عند إرسال القوانين، سيظهر للمستخدمين أزرار تفاعلية يمكنهم الضغط عليها لاختيار فئة القوانين المطلوبة!</p>
        </div>
        
        <div class="bot-status" id="botStatus">
            <i class="fas fa-robot"></i> حالة البوت: <span id="statusText">متصل</span>
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
                <div class="stat-number">{{ stats.total_rules }}</div>
                <div class="stat-label">إجمالي القوانين</div>
            </div>
        </div>
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('send-rules')">إرسال القوانين</button>
            <button class="tab" onclick="showTab('manage-rules')">إدارة القوانين</button>
        </div>
        
        <!-- تبويب إرسال القوانين -->
        <div id="send-rules" class="tab-content active">
            <div class="card">
                <div class="card-header">
                    <i class="fas fa-paper-plane"></i>
                    إرسال رسالة القوانين التفاعلية
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
                        </div>
                    </div>
                    
                    <button class="btn" onclick="sendInteractiveRules()">
                        <i class="fas fa-paper-plane"></i> إرسال القوانين التفاعلية
                    </button>
                </div>
            </div>
        </div>
        
        <!-- تبويب إدارة القوانين -->
        <div id="manage-rules" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <i class="fas fa-cog"></i>
                    إدارة القوانين
                </div>
                <div class="card-body">
                    <div class="form-group">
                        <label>فئات القوانين الحالية:</label>
                        <div id="categoriesList"></div>
                    </div>
                    
                    <button class="btn" onclick="showAddCategoryModal()">
                        <i class="fas fa-plus"></i> إضافة فئة جديدة
                    </button>
                </div>
            </div>
        </div>
        
        <!-- نافذة إضافة فئة -->
        <div id="addCategoryModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000;">
            <div style="background: white; padding: 30px; border-radius: 12px; max-width: 500px; margin: 100px auto; position: relative;">
                <h3 style="margin-bottom: 20px;">إضافة فئة قوانين جديدة</h3>
                <div class="form-group">
                    <label>اسم الفئة:</label>
                    <input type="text" id="newCategoryName" placeholder="مثال: قوانين الألعاب">
                </div>
                <div class="form-group">
                    <label>القوانين (كل قانون في سطر جديد):</label>
                    <textarea id="newCategoryRules" placeholder="🚫 ممنوع الغش&#10;🤝 احترام اللاعبين&#10;🏆 قبول الهزيمة"></textarea>
                </div>
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button class="btn" onclick="addCategory()">إضافة</button>
                    <button class="btn btn-secondary" onclick="closeModal()">إلغاء</button>
                </div>
            </div>
        </div>
        
        <!-- نافذة تعديل فئة -->
        <div id="editCategoryModal" style="display: none; position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); z-index: 1000;">
            <div style="background: white; padding: 30px; border-radius: 12px; max-width: 500px; margin: 100px auto; position: relative;">
                <h3 style="margin-bottom: 20px;">تعديل فئة القوانين</h3>
                <div class="form-group">
                    <label>اسم الفئة:</label>
                    <input type="text" id="editCategoryName" placeholder="مثال: قوانين الألعاب">
                </div>
                <div class="form-group">
                    <label>القوانين (كل قانون في سطر جديد):</label>
                    <textarea id="editCategoryRules" placeholder="🚫 ممنوع الغش&#10;🤝 احترام اللاعبين&#10;🏆 قبول الهزيمة"></textarea>
                </div>
                <div style="display: flex; gap: 10px; margin-top: 20px;">
                    <button class="btn" onclick="updateCategory()">حفظ التعديلات</button>
                    <button class="btn btn-secondary" onclick="closeEditModal()">إلغاء</button>
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
            
            function sendInteractiveRules() {
                const channelId = document.getElementById('channelSelect').value;
                
                if (!channelId) {
                    alert('يرجى اختيار القناة أولاً');
                    return;
                }
                
                fetch('/api/send-interactive-rules', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ channel_id: channelId })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('تم إرسال رسالة القوانين التفاعلية بنجاح!');
                    } else {
                        alert('خطأ: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('حدث خطأ أثناء إرسال رسالة القوانين التفاعلية');
                });
            }
            
            // فحص حالة البوت
            function updateBotStatus() {
                fetch('/api/bot-status')
                    .then(response => response.json())
                    .then(data => {
                        const botStatus = document.getElementById('botStatus');
                        const statusText = document.getElementById('statusText');
                        
                        if (data.connected) {
                            botStatus.classList.remove('disconnected');
                            statusText.textContent = 'متصل';
                        } else {
                            botStatus.classList.add('disconnected');
                            statusText.textContent = 'غير متصل';
                        }
                    })
                    .catch(error => {
                        console.error('Error checking bot status:', error);
                    });
            }
            
            // تحديث حالة البوت كل 5 ثواني
            setInterval(updateBotStatus, 5000);
            
            // تحديث الحالة فوراً
            updateBotStatus();
            
            // تبويبات
            function showTab(tabId) {
                const tabs = document.querySelectorAll('.tab');
                const tabContents = document.querySelectorAll('.tab-content');
                
                tabs.forEach(tab => tab.classList.remove('active'));
                tabContents.forEach(content => content.classList.remove('active'));
                
                document.getElementById(tabId).classList.add('active');
                document.querySelector(`[onclick="showTab('${tabId}')"]`).classList.add('active');
            }
            
            // إضافة فئة جديدة
            function showAddCategoryModal() {
                document.getElementById('addCategoryModal').style.display = 'block';
            }
            
            function closeModal() {
                document.getElementById('addCategoryModal').style.display = 'none';
            }
            
            function addCategory() {
                const categoryName = document.getElementById('newCategoryName').value;
                const categoryRules = document.getElementById('newCategoryRules').value;
                
                if (!categoryName || !categoryRules) {
                    alert('يرجى ملء جميع الحقول!');
                    return;
                }
                
                const rules = categoryRules.split('\\n').filter(rule => rule.trim());
                
                fetch('/api/rules', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ category_name: categoryName, rules })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('تم إضافة الفئة بنجاح!');
                        closeModal();
                        loadCategories();
                    } else {
                        alert('خطأ: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('حدث خطأ أثناء إضافة الفئة');
                });
            }
            
            // تعديل فئة
            function showEditCategoryModal(categoryName, categoryRules) {
                document.getElementById('editCategoryName').value = categoryName;
                document.getElementById('editCategoryRules').value = categoryRules;
                document.getElementById('editCategoryModal').style.display = 'block';
            }
            
            function closeEditModal() {
                document.getElementById('editCategoryModal').style.display = 'none';
            }
            
            function updateCategory() {
                const categoryName = document.getElementById('editCategoryName').value;
                const categoryRules = document.getElementById('editCategoryRules').value;
                
                if (!categoryName || !categoryRules) {
                    alert('يرجى ملء جميع الحقول!');
                    return;
                }
                
                const rules = categoryRules.split('\\n').filter(rule => rule.trim());
                
                fetch(`/api/rules/${categoryName}`, {
                    method: 'PUT',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ category_name: categoryName, rules })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        alert('تم تحديث الفئة بنجاح!');
                        closeEditModal();
                        loadCategories();
                    } else {
                        alert('خطأ: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('حدث خطأ أثناء تحديث الفئة');
                });
            }
            
            // تحميل الفئات عند فتح تبويب الإدارة
            function loadCategories() {
                fetch('/api/rules')
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            displayCategories(data.rules);
                        }
                    })
                    .catch(error => {
                        console.error('Error loading categories:', error);
                    });
            }
            
            function displayCategories(rules) {
                const categoriesList = document.getElementById('categoriesList');
                categoriesList.innerHTML = '';
                
                for (const [category, categoryRules] of Object.entries(rules)) {
                    const categoryDiv = document.createElement('div');
                    categoryDiv.style.background = '#f8f9fa';
                    categoryDiv.style.padding = '15px';
                    categoryDiv.style.borderRadius = '8px';
                    categoryDiv.style.marginBottom = '10px';
                    categoryDiv.style.border = '1px solid #dee2e6';
                    
                    categoryDiv.innerHTML = `
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                            <strong style="color: #667eea; font-size: 16px;">${category}</strong>
                            <div>
                                <button class="btn" style="padding: 5px 10px; font-size: 12px;" onclick="showEditCategoryModal('${category}', \`${categoryRules.join('\\n')}\`)">تعديل</button>
                                <button class="btn btn-secondary" style="padding: 5px 10px; font-size: 12px; background: linear-gradient(135deg, #dc3545 0%, #c82333 100%);" onclick="deleteCategory('${category}')">حذف</button>
                            </div>
                        </div>
                        <div style="color: #666; font-size: 14px;">
                            <strong>عدد القوانين:</strong> ${categoryRules.length}
                        </div>
                    `;
                    
                    categoriesList.appendChild(categoryDiv);
                }
            }
            
            // حذف فئة
            function deleteCategory(categoryName) {
                if (confirm(`هل أنت متأكد من حذف فئة "${categoryName}"؟`)) {
                    fetch(`/api/rules/${categoryName}`, {
                        method: 'DELETE'
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.success) {
                            alert('تم حذف الفئة بنجاح!');
                            loadCategories();
                        } else {
                            alert('خطأ: ' + data.error);
                        }
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('حدث خطأ أثناء حذف الفئة');
                    });
                }
            }
            
            // تحميل الفئات عند فتح التبويب
            document.querySelector('[onclick="showTab(\'manage-rules\')"]').addEventListener('click', loadCategories);
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
    guilds = []
    for guild in bot.guilds:
        guilds.append({
            'id': str(guild.id),
            'name': guild.name
        })
    
    # تحميل القوانين الحالية
    current_rules = load_rules()
    
    # حساب الإحصائيات
    total_servers = len(guilds)
    total_channels = sum(len(guild.channels) for guild in bot.guilds)
    total_rules = sum(len(rules) for rules in current_rules.values())
    
    stats = {
        'total_servers': total_servers,
        'total_channels': total_channels,
        'rules_count': len(current_rules),
        'total_rules': total_rules
    }
    
    return render_template_string(INTERACTIVE_DASHBOARD, 
                              servers=guilds, 
                              stats=stats, 
                              rules=current_rules)

@app.route('/api/servers/<server_id>/channels')
def api_server_channels(server_id):
    if 'logged_in' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    
    guild = bot.get_guild(int(server_id))
    if not guild:
        return jsonify([])
    
    channels = []
    for channel in guild.text_channels:
        channels.append({
            'id': str(channel.id),
            'name': channel.name,
            'type': 0
        })
    
    return jsonify(channels)

@app.route('/api/send-interactive-rules', methods=['POST'])
def api_send_interactive_rules():
    if 'logged_in' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    
    try:
        data = request.get_json()
        channel_id = data.get('channel_id')
        
        if not channel_id:
            return jsonify({'success': False, 'error': 'لم يتم تحديد القناة'})
        
        # إرسال القوانين التفاعلية
        channel = bot.get_channel(int(channel_id))
        if not channel:
            return jsonify({'success': False, 'error': 'القناة غير موجودة'})
        
        rules = load_rules()
        view = RulesView(rules)
        
        embed = discord.Embed(
            title="📜 اختر فئة القوانين",
            description="مرحباً بك! 🎊\n\nاختر فئة القوانين التي تريد مشاهدتها:",
            color=0x667eea
        )
        
        asyncio.run_coroutine_threadsafe(channel.send(embed=embed, view=view), bot.loop)
        
        return jsonify({'success': True, 'message': 'تم إرسال القوانين التفاعلية بنجاح'})
    except Exception as e:
        logger.error(f"Error in send_interactive_rules API: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/rules', methods=['GET'])
def api_get_rules():
    """الحصول على جميع القوانين"""
    if 'logged_in' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    rules = load_rules()
    return jsonify({'success': True, 'rules': rules})

@app.route('/api/rules', methods=['POST'])
def api_add_category():
    """إضافة فئة قوانين جديدة"""
    if 'logged_in' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    
    try:
        data = request.get_json()
        category_name = data.get('category_name')
        rules = data.get('rules', [])
        
        if not category_name:
            return jsonify({'success': False, 'error': 'لم يتم تحديد اسم الفئة'})
        
        if not rules:
            return jsonify({'success': False, 'error': 'لم يتم تحديد القوانين'})
        
        # تحميل القوانين الحالية
        current_rules = load_rules()
        
        # إضافة الفئة الجديدة
        current_rules[category_name] = rules
        
        # حفظ القوانين
        if save_rules(current_rules):
            return jsonify({'success': True, 'message': 'تم إضافة الفئة بنجاح'})
        else:
            return jsonify({'success': False, 'error': 'فشل في حفظ القوانين'})
            
    except Exception as e:
        logger.error(f"Error in add_category API: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/rules/<category_name>', methods=['PUT'])
def api_update_category(category_name):
    """تعديل فئة قوانين موجودة"""
    if 'logged_in' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    
    try:
        data = request.get_json()
        new_rules = data.get('rules', [])
        new_category_name = data.get('category_name')
        
        if not new_rules:
            return jsonify({'success': False, 'error': 'لم يتم تحديد القوانين'})
        
        # تحميل القوانين الحالية
        current_rules = load_rules()
        
        # حذف الفئة القديمة إذا تم تغيير الاسم
        if new_category_name and new_category_name != category_name:
            if category_name in current_rules:
                del current_rules[category_name]
            category_name = new_category_name
        
        # تحديث الفئة
        current_rules[category_name] = new_rules
        
        # حفظ القوانين
        if save_rules(current_rules):
            return jsonify({'success': True, 'message': 'تم تحديث الفئة بنجاح'})
        else:
            return jsonify({'success': False, 'error': 'فشل في حفظ القوانين'})
            
    except Exception as e:
        logger.error(f"Error in update_category API: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/rules/<category_name>', methods=['DELETE'])
def api_delete_category(category_name):
    """حذف فئة قوانين"""
    if 'logged_in' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    
    try:
        # تحميل القوانين الحالية
        current_rules = load_rules()
        
        # حذف الفئة
        if category_name in current_rules:
            del current_rules[category_name]
            
            # حفظ القوانين
            if save_rules(current_rules):
                return jsonify({'success': True, 'message': 'تم حذف الفئة بنجاح'})
            else:
                return jsonify({'success': False, 'error': 'فشل في حفظ القوانين'})
        else:
            return jsonify({'success': False, 'error': 'الفئة غير موجودة'})
            
    except Exception as e:
        logger.error(f"Error in delete_category API: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/bot-status')
def api_bot_status():
    """فحص حالة البوت"""
    return jsonify({
        'connected': bot.is_ready(),
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
        "bot_connected": bot.is_ready(),
        "rules_count": len(load_rules()),
        "total_rules": sum(len(rules) for rules in load_rules().values())
    })

def run_flask():
    """تشغيل Flask في خيط منفصل"""
    app.run(host='0.0.0.0', port=int(os.getenv('PORT', 3000)), debug=False)

if __name__ == "__main__":
    # تشغيل Flask في خيط منفصل
    flask_thread = Thread(target=run_flask)
    flask_thread.daemon = True
    flask_thread.start()
    
    # تشغيل البوت
    if BOT_TOKEN:
        logger.info("✅ بدء تشغيل البوت...")
        bot.run(BOT_TOKEN)
    else:
        logger.error("❌ DISCORD_TOKEN غير موجود!")
