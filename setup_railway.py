#!/usr/bin/env python3
"""
سكربت إعداد متغيرات البيئة لـ Railway
"""
import os

def setup_environment():
    """إعداد متغيرات البيئة المطلوبة"""
    
    required_vars = {
        'DISCORD_TOKEN': 'توكن بوت ديسكورد',
        'APPLICATION_ID': 'معرف تطبيق البوت',
        'GUILD_ID': 'معرف السيرفر'
    }
    
    print("🔧 إعداد متغيرات البيئة لـ Railway")
    print("=" * 50)
    
    for var, description in required_vars.items():
        value = os.getenv(var)
        if value:
            print(f"✅ {var}: تم تعيينه")
        else:
            print(f"❌ {var}: غير معين - {description}")
    
    print("\n📋 في Railway، أضف هذه المتغيرات في قسم Variables:")
    for var, description in required_vars.items():
        print(f"   • {var} - {description}")
    
    print("\n🔑 للحصول على هذه القيم:")
    print("1. اذهب إلى Discord Developer Portal")
    print("2. اختر تطبيق البوت")
    print("3. من Bot section احصل على التوكن")
    print("4. من General Information احصل على APPLICATION_ID")
    print("5. من السيرفر في ديسكورد، تفعيل Developer Mode")
    print("6. كلك يمين على السيرفر > Copy Server ID")

if __name__ == "__main__":
    setup_environment()
