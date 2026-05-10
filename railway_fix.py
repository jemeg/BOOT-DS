#!/usr/bin/env python3
"""
سكربت إصلاح مشكلة audioop في Railway
"""
import subprocess
import sys

def fix_audioop():
    """إصلاح مشكلة audioop"""
    try:
        # تثبيت إصدار أقدم من discord.py لا يعتمد على audioop
        subprocess.check_call([
            sys.executable, "-m", "pip", "install", 
            "discord.py==2.3.2", "--no-deps"
        ])
        
        # تثبيت المكتبات المطلوبة يدوياً
        subprocess.check_call([
            sys.executable, "-m", "pip", "install",
            "aiohttp", "websockets", "typing-extensions"
        ])
        
        print("✅ تم إصلاح مشكلة audioop بنجاح!")
        
    except subprocess.CalledProcessError as e:
        print(f"❌ فشل الإصلاح: {e}")
        return False
    
    return True

if __name__ == "__main__":
    fix_audioop()
