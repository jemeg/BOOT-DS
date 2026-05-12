import redis
import os
import json
import logging
from datetime import timedelta

# إعداد الـ logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class RedisManager:
    def __init__(self):
        self.redis_client = None
        self.redis_url = os.getenv('REDIS_URL')
        self.connected = False
        
    def connect(self):
        """الاتصال بـ Redis"""
        try:
            if self.redis_url:
                self.redis_client = redis.from_url(self.redis_url)
                # اختبار الاتصال
                self.redis_client.ping()
                self.connected = True
                logger.info("✅ تم الاتصال بـ Redis بنجاح")
                return True
            else:
                logger.warning("⚠️ REDIS_URL غير موجود - سيتم استخدام التخزين المؤقت المحلي")
                return False
        except Exception as e:
            logger.error(f"❌ خطأ في الاتصال بـ Redis: {e}")
            return False
    
    def set_cache(self, key, value, expire_seconds=300):
        """تخزين قيمة في Redis"""
        if self.connected and self.redis_client:
            try:
                self.redis_client.setex(key, expire_seconds, json.dumps(value))
                return True
            except Exception as e:
                logger.error(f"❌ خطأ في تخزين البيانات: {e}")
        return False
    
    def get_cache(self, key):
        """جلب قيمة من Redis"""
        if self.connected and self.redis_client:
            try:
                value = self.redis_client.get(key)
                if value:
                    return json.loads(value)
            except Exception as e:
                logger.error(f"❌ خطأ في جلب البيانات: {e}")
        return None
    
    def delete_cache(self, key):
        """حذف قيمة من Redis"""
        if self.connected and self.redis_client:
            try:
                self.redis_client.delete(key)
                return True
            except Exception as e:
                logger.error(f"❌ خطأ في حذف البيانات: {e}")
        return False
    
    def clear_all_cache(self):
        """مسح كل البيانات"""
        if self.connected and self.redis_client:
            try:
                self.redis_client.flushdb()
                logger.info("✅ تم مسح كل البيانات بنجاح")
                return True
            except Exception as e:
                logger.error(f"❌ خطأ في مسح البيانات: {e}")
        return False

# إنشاء مدير Redis
redis_manager = RedisManager()

# محاولة الاتصال عند بدء التشغيل
redis_manager.connect()
