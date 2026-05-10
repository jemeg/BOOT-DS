# بوت ديسكورد لعرض القوانين ثلاثية الأبعاد

## المميزات
- ✅ يعمل بدون خادم (مجاني)
- 🎮 عرض القوانين عند دخول الروم الصوتي
- 📜 رسائل ثلاثية الأبعاد جميلة
- 🔄 قابلة للتحديث والتعديل

## طريقة التركيب

### 1. إنشاء بوت ديسكورد
1. اذهب إلى [Discord Developer Portal](https://discord.com/developers/applications)
2. اضغط "New Application"
3. أعطِ البوت اسمًا
4. اذهب إلى "Bot" ثم "Add Bot"
5. انسخ الـ Token

### 2. إعطاء الصلاحيات
1. في Developer Portal اذهب إلى "OAuth2" -> "URL Generator"
2. اختر الصلاحيات:
   - `bot`
   - `applications.commands`
3. في Bot Permissions اختر:
   - `Send Messages`
   - `Embed Links`
   - `Read Message History`
   - `Connect`
   - `Speak`

### 3. الرفع على Replit (مجاناً)

1. اذهب إلى [replit.com](https://replit.com)
2. أنشئ حساب جديد
3. اضغط "Create Repl"
4. اختر "Python" كنوع المشروع
5. ارفع الملفات الثلاثة:
   - `discord_bot.py`
   - `keep_alive.py` 
   - `requirements.txt`

6. في Replit:
   - اذهب إلى "Secrets" (أيقونة القفل)
   - أضف سر جديد:
     - Key: `DISCORD_TOKEN`
     - Value: ضع توكن البوت هنا

7. اضغط "Run" لتشغيل البوت

### 4. إضافة البوت للسيرفر
1. استخدم رابط OAuth من Developer Portal
2. اختر السيرفر الذي تريد إضافة البوت إليه
3. اضغط "Authorize"

## الأوامر
- `!قوانين` - عرض القوانين
- `!تحديث_القوانين [نص]` - تحديث القوانين (للمشرفين فقط)

## تعديل القوانين
في ملف `discord_bot.py` عدّل متغير `RULES`:

```python
RULES = [
    "📜 **القانون الأول**: القانون هنا",
    "📜 **القانون الثاني**: القانون الثاني هنا",
    # أضف المزيد من القوانين
]
```

## تغيير الصورة ثلاثية الأبعاد
في ملف `discord_bot.py` غيّر الرابط:
```python
embed.set_image(url="رابط_الصورة_هنا")
```

## ملاحظات
- البوت يعمل 24/7 على Replit مجاناً
- يمكنك استخدام Glitch بدلاً من Replit
- تأكد من إعطاء البوت الصلاحيات الصحيحة
