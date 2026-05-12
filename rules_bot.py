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
from redis_setup import redis_manager

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

# ملف تخزين القوانين
RULES_FILE = 'rules_data.json'

# القوانين الافتراضية
DEFAULT_RULES = [
    "🚫 ممنوع السب والشتم",
    "🚫 ممنوع نشر الروابط بدون إذن",
    "🚫 ممنوع إزعاج الأعضاء",
    "🚫 ممنوع نشر محتوى غير لائق",
    "📝 احترام الجميع مطلوب",
    "🎮 الالتزام بقوانين اللعب"
]

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
        <div class="bot-info"><p>لوحة تحكم بوت القوانين الذكي</p></div>
    </div>
</body>
</html>
"""

RULES_DASHBOARD_TEMPLATE = """
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
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 30px;
            border-bottom: 2px solid #ddd;
        }
        .tab {
            padding: 12px 24px;
            background: none;
            border: none;
            cursor: pointer;
            font-size: 16px;
            font-weight: 500;
            color: #666;
            border-bottom: 3px solid transparent;
            transition: all 0.3s;
        }
        .tab.active {
            color: #667eea;
            border-bottom-color: #667eea;
        }
        .tab-content {
            display: none;
        }
        .tab-content.active {
            display: block;
        }
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
        .btn-danger {
            background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        }
        .btn-success {
            background: linear-gradient(135deg, #27ae60 0%, #229954 100%);
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
        .icon-btn.edit {
            background: #3498db;
            color: white;
        }
        .icon-btn.delete {
            background: #e74c3c;
            color: white;
        }
        .icon-btn:hover {
            transform: scale(1.1);
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
        .modal {
            display: none;
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0,0,0,0.5);
            z-index: 1000;
        }
        .modal-content {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 30px;
            border-radius: 12px;
            max-width: 500px;
            width: 90%;
        }
        .modal-header {
            margin-bottom: 20px;
        }
        .modal-title {
            font-size: 20px;
            font-weight: bold;
            color: #333;
        }
        .modal-body { margin-bottom: 20px; }
        .modal-footer {
            display: flex;
            gap: 10px;
            justify-content: flex-end;
        }
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
        
        <div class="tabs">
            <button class="tab active" onclick="showTab('rules')">القوانين</button>
            <button class="tab" onclick="showTab('channels')">القنوات</button>
            <button class="tab" onclick="showTab('settings')">الإعدادات</button>
        </div>
        
        <div id="rules" class="tab-content active">
            <div class="card">
                <div class="card-header">
                    <i class="fas fa-gavel"></i>
                    إدارة القوانين
                </div>
                <div class="card-body">
                    <div class="form-group">
                        <label>إضافة قانون جديد:</label>
                        <div style="display: flex; gap: 10px;">
                            <input type="text" id="newRule" placeholder="اكتب القانون الجديد..." style="flex: 1;">
                            <button class="btn btn-success" onclick="addRule()">
                                <i class="fas fa-plus"></i> إضافة
                            </button>
                        </div>
                    </div>
                    
                    <div class="rules-list" id="rulesList">
                        <!-- سيتم ملؤها بواسطة JavaScript -->
                    </div>
                </div>
            </div>
        </div>
        
        <div id="channels" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <i class="fas fa-hashtag"></i>
                    القنوات النشطة
                </div>
                <div class="card-body">
                    <div id="channelsList">
                        <!-- سيتم ملؤها بواسطة JavaScript -->
                    </div>
                </div>
            </div>
        </div>
        
        <div id="settings" class="tab-content">
            <div class="card">
                <div class="card-header">
                    <i class="fas fa-cog"></i>
                    الإعدادات
                </div>
                <div class="card-body">
                    <div class="form-group">
                        <label>رسالة الترحيب:</label>
                        <textarea id="welcomeMessage" placeholder="رسالة الترحيب الافتراضية...">مرحباً بك في السيرفر! يرجى قراءة القوانين أدناه:</textarea>
                    </div>
                    <div class="form-group">
                        <label>صورة القوانين (URL):</label>
                        <input type="url" id="rulesImage" placeholder="https://example.com/rules.png">
                    </div>
                    <div class="form-group">
                        <label>لون الرسالة:</label>
                        <input type="color" id="embedColor" value="#667eea">
                    </div>
                    <button class="btn" onclick="saveSettings()">حفظ الإعدادات</button>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Modal لتعديل القوانين -->
    <div id="editModal" class="modal">
        <div class="modal-content">
            <div class="modal-header">
                <h3 class="modal-title">تعديل القانون</h3>
            </div>
            <div class="modal-body">
                <input type="text" id="editRuleText" style="width: 100%; padding: 10px; border: 1px solid #ddd; border-radius: 5px;">
            </div>
            <div class="modal-footer">
                <button class="btn" onclick="saveEditRule()">حفظ</button>
                <button class="btn btn-danger" onclick="closeEditModal()">إلغاء</button>
            </div>
        </div>
    </div>
    
    <script>
        let currentRules = [];
        let currentSettings = {};
        let editingIndex = -1;
        
        function showTab(tabName) {
            // إخفاء كل التبويبات
            document.querySelectorAll('.tab-content').forEach(tab => {
                tab.classList.remove('active');
            });
            document.querySelectorAll('.tab').forEach(tab => {
                tab.classList.remove('active');
            });
            
            // إظهار التبويب المطلوب
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
            
            // تحميل البيانات حسب التبويب
            if (tabName === 'rules') {
                loadRules();
            } else if (tabName === 'channels') {
                loadChannels();
            } else if (tabName === 'settings') {
                loadSettings();
            }
        }
        
        function loadRules() {
            fetch('/api/rules')
                .then(response => response.json())
                .then(data => {
                    currentRules = data.rules || [];
                    displayRules();
                })
                .catch(error => {
                    console.error('Error loading rules:', error);
                });
        }
        
        function displayRules() {
            const container = document.getElementById('rulesList');
            container.innerHTML = currentRules.map((rule, index) => `
                <div class="rule-item">
                    <div class="rule-number">${index + 1}</div>
                    <div class="rule-text">${rule}</div>
                    <div class="rule-actions">
                        <button class="icon-btn edit" onclick="editRule(${index})">
                            <i class="fas fa-edit"></i>
                        </button>
                        <button class="icon-btn delete" onclick="deleteRule(${index})">
                            <i class="fas fa-trash"></i>
                        </button>
                    </div>
                </div>
            `).join('');
        }
        
        function addRule() {
            const input = document.getElementById('newRule');
            const ruleText = input.value.trim();
            
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
                    input.value = '';
                    loadRules();
                } else {
                    alert('خطأ: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('حدث خطأ أثناء إضافة القانون');
            });
        }
        
        function editRule(index) {
            editingIndex = index;
            document.getElementById('editRuleText').value = currentRules[index];
            document.getElementById('editModal').style.display = 'block';
        }
        
        function saveEditRule() {
            const newText = document.getElementById('editRuleText').value.trim();
            
            if (!newText) {
                alert('يرجى كتابة القانون');
                return;
            }
            
            fetch('/api/rules', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    action: 'edit',
                    index: editingIndex,
                    rule: newText
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    closeEditModal();
                    loadRules();
                } else {
                    alert('خطأ: ' + data.error);
                }
            })
            .catch(error => {
                console.error('Error:', error);
                alert('حدث خطأ أثناء تعديل القانون');
            });
        }
        
        function closeEditModal() {
            document.getElementById('editModal').style.display = 'none';
            editingIndex = -1;
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
                        loadRules();
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
        
        function loadChannels() {
            fetch('/api/rules-channels')
                .then(response => response.json())
                .then(data => {
                    displayChannels(data.channels || []);
                })
                .catch(error => {
                    console.error('Error loading channels:', error);
                });
        }
        
        function displayChannels(channels) {
            const container = document.getElementById('channelsList');
            if (channels.length === 0) {
                container.innerHTML = '<p>لا توجد قنوات مفعلة للقوانين حالياً</p>';
                return;
            }
            
            container.innerHTML = `
                <div style="display: grid; gap: 15px;">
                    ${channels.map(channel => `
                        <div style="background: #f8f9fa; padding: 15px; border-radius: 8px; display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <strong>#${channel.name}</strong>
                                <br>
                                <small style="color: #666;">السيرفر: ${channel.server_name}</small>
                            </div>
                            <button class="btn btn-danger" onclick="removeChannel('${channel.id}')">
                                إزالة
                            </button>
                        </div>
                    `).join('')}
                </div>
            `;
        }
        
        function removeChannel(channelId) {
            if (confirm('هل أنت متأكد من إزالة هذه القناة؟')) {
                fetch('/api/rules-channels', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        action: 'remove',
                        channel_id: channelId
                    })
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        loadChannels();
                    } else {
                        alert('خطأ: ' + data.error);
                    }
                })
                .catch(error => {
                    console.error('Error:', error);
                    alert('حدث خطأ أثناء إزالة القناة');
                });
            }
        }
        
        function loadSettings() {
            fetch('/api/settings')
                .then(response => response.json())
                .then(data => {
                    currentSettings = data.settings || {};
                    document.getElementById('welcomeMessage').value = currentSettings.welcome_message || 'مرحباً بك في السيرفر! يرجى قراءة القوانين أدناه:';
                    document.getElementById('rulesImage').value = currentSettings.rules_image || '';
                    document.getElementById('embedColor').value = currentSettings.embed_color || '#667eea';
                })
                .catch(error => {
                    console.error('Error loading settings:', error);
                });
        }
        
        function saveSettings() {
            const settings = {
                welcome_message: document.getElementById('welcomeMessage').value,
                rules_image: document.getElementById('rulesImage').value,
                embed_color: document.getElementById('embedColor').value
            };
            
            fetch('/api/settings', {
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
        
        // تحميل القوانين عند بدء التشغيل
        loadRules();
    </script>
</body>
</html>
"""

class RulesManager:
    def __init__(self):
        self.rules_file = RULES_FILE
        self.settings_file = 'rules_settings.json'
        self.channels_file = 'rules_channels.json'
        self.data = self.load_data()
        self.settings = self.load_settings()
        self.channels = self.load_channels()
        
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
    
    def load_settings(self):
        """تحميل إعدادات القوانين"""
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return {
                    'welcome_message': 'مرحباً بك في السيرفر! يرجى قراءة القوانين أدناه:',
                    'rules_image': 'https://i.imgur.com/3D-rules-example.png',
                    'embed_color': '#667eea'
                }
        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            return {
                'welcome_message': 'مرحباً بك في السيرفر! يرجى قراءة القوانين أدناه:',
                'rules_image': 'https://i.imgur.com/3D-rules-example.png',
                'embed_color': '#667eea'
            }
    
    def save_settings(self):
        """حفظ إعدادات القوانين"""
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            return False
    
    def load_channels(self):
        """تحميل القنوات المفعلة"""
        try:
            if os.path.exists(self.channels_file):
                with open(self.channels_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            else:
                return []
        except Exception as e:
            logger.error(f"Error loading channels: {e}")
            return []
    
    def save_channels(self):
        """حفظ القنوات المفعلة"""
        try:
            with open(self.channels_file, 'w', encoding='utf-8') as f:
                json.dump(self.channels, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            logger.error(f"Error saving channels: {e}")
            return False
    
    def add_rule(self, rule_text):
        """إضافة قانون جديد"""
        self.data['rules'].append(rule_text)
        return self.save_data()
    
    def edit_rule(self, index, new_text):
        """تعديل قانون"""
        if 0 <= index < len(self.data['rules']):
            self.data['rules'][index] = new_text
            return self.save_data()
        return False
    
    def delete_rule(self, index):
        """حذف قانون"""
        if 0 <= index < len(self.data['rules']):
            del self.data['rules'][index]
            return self.save_data()
        return False
    
    def add_channel(self, channel_id, server_name, channel_name):
        """إضافة قناة مفعلة"""
        # التحقق من عدم وجود القناة مسبقاً
        for channel in self.channels:
            if channel['id'] == channel_id:
                return False
        
        self.channels.append({
            'id': channel_id,
            'server_name': server_name,
            'channel_name': channel_name,
            'added_at': datetime.now().isoformat()
        })
        return self.save_channels()
    
    def remove_channel(self, channel_id):
        """إزالة قناة مفعلة"""
        self.channels = [ch for ch in self.channels if ch['id'] != channel_id]
        return self.save_channels()
    
    def get_rules_embed(self, member_name=None):
        """إنشاء رسالة القوانين"""
        rules_text = '\n'.join([f"**{i+1}.** {rule}" for i, rule in enumerate(self.data['rules'])])
        
        embed = {
            "title": "📜 قوانين السيرفر",
            "description": f"{self.settings['welcome_message']}\n\n{rules_text}",
            "color": int(self.settings['embed_color'].replace('#', ''), 16),
            "footer": {"text": f"مرحباً {member_name or 'بك'}!"}
        }
        
        if self.settings['rules_image']:
            embed["image"] = {"url": self.settings['rules_image']}
        
        return embed

class DiscordWebBot:
    def __init__(self):
        self.token = BOT_TOKEN
        self.application_id = APPLICATION_ID
        self.guild_id = GUILD_ID
        self.base_url = "https://discord.com/api/v10"
        self.headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json",
            "User-Agent": "DiscordBot (Render, 1.0)"
        }
        self.rules_manager = RulesManager()
        self.user_rules_messages = {}  # لتتبع رسائل القوانين لكل مستخدم
        
    def test_connection(self):
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
    
    def delete_message(self, channel_id, message_id):
        """حذف رسالة معينة"""
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
    
    def get_user_guilds(self):
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
    
    def get_guild_info(self, guild_id):
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

# إنشاء كائنات
discord_bot = DiscordWebBot()
rules_manager = discord_bot.rules_manager

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
    return render_template_string(RULES_DASHBOARD_TEMPLATE)

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
            if rule_text and rules_manager.add_rule(rule_text):
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'فشل في إضافة القانون'})
        
        elif action == 'edit':
            index = data.get('index')
            new_text = data.get('rule', '').strip()
            if new_text and rules_manager.edit_rule(index, new_text):
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'فشل في تعديل القانون'})
        
        elif action == 'delete':
            index = data.get('index')
            if rules_manager.delete_rule(index):
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'فشل في حذف القانون'})
        
        return jsonify({'success': False, 'error': 'إجراء غير صالح'})

@app.route('/api/rules-channels', methods=['GET', 'POST'])
def api_rules_channels():
    if 'logged_in' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    
    if request.method == 'GET':
        # إضافة معلومات السيرفرات
        guilds = discord_bot.get_user_guilds()
        guild_info = {guild['id']: guild['name'] for guild in guilds}
        
        channels_with_info = []
        for channel in rules_manager.channels:
            channel_info = channel.copy()
            channel_info['server_name'] = guild_info.get(channel['server_name'], channel['server_name'])
            channels_with_info.append(channel_info)
        
        return jsonify({'channels': channels_with_info})
    
    if request.method == 'POST':
        data = request.get_json()
        action = data.get('action')
        
        if action == 'add':
            channel_id = data.get('channel_id')
            server_name = data.get('server_name')
            channel_name = data.get('channel_name')
            
            if rules_manager.add_channel(channel_id, server_name, channel_name):
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'فشل في إضافة القناة'})
        
        elif action == 'remove':
            channel_id = data.get('channel_id')
            if rules_manager.remove_channel(channel_id):
                return jsonify({'success': True})
            else:
                return jsonify({'success': False, 'error': 'فشل في إزالة القناة'})
        
        return jsonify({'success': False, 'error': 'إجراء غير صالح'})

@app.route('/api/settings', methods=['GET', 'POST'])
def api_settings():
    if 'logged_in' not in session:
        return jsonify({'error': 'غير مصرح'}), 401
    
    if request.method == 'GET':
        return jsonify({'settings': rules_manager.settings})
    
    if request.method == 'POST':
        settings = request.get_json()
        rules_manager.settings.update(settings)
        if rules_manager.save_settings():
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'فشل في حفظ الإعدادات'})

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
        "bot_connected": discord_bot.test_connection()[0],
        "rules_count": len(rules_manager.data['rules']),
        "active_channels": len(rules_manager.channels)
    })

if __name__ == "__main__":
    # اختبار الاتصال
    connected, bot_info = discord_bot.test_connection()
    if connected:
        logger.info("✅ بوت القوانين متصل وجاهز للعمل")
        
        # بدء WebSocket للقوانين
        try:
            from rules_websocket import start_rules_websocket
            websocket_started = start_rules_websocket()
            if websocket_started:
                logger.info("✅ WebSocket للقوانين بدأ العمل")
            else:
                logger.warning("⚠️ WebSocket للقوانين لم يبدأ العمل - البوت سيعمل بدون مراقبة الصوت")
        except Exception as e:
            logger.error(f"❌ خطأ في بدء WebSocket: {e}")
        
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)), debug=False)
    else:
        logger.error("❌ فشل الاتصال بالبوت")
        app.run(host='0.0.0.0', port=int(os.getenv('PORT', 8080)), debug=False)
