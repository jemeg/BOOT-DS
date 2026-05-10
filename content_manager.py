#!/usr/bin/env python3
"""
مدير المحتوى للبوت - واجهة لإدارة المحتوى لكل روم
"""
import json
import os
from datetime import datetime

class ContentManager:
    def __init__(self):
        self.data_file = 'channels_data.json'
        self.load_data()
    
    def load_data(self):
        """تحميل بيانات القنوات"""
        try:
            if os.path.exists(self.data_file):
                with open(self.data_file, 'r', encoding='utf-8') as f:
                    self.data = json.load(f)
            else:
                self.data = {}
        except Exception as e:
            print(f"❌ خطأ في تحميل البيانات: {e}")
            self.data = {}
    
    def save_data(self):
        """حفظ بيانات القنوات"""
        try:
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            print("✅ تم حفظ البيانات بنجاح")
        except Exception as e:
            print(f"❌ خطأ في حفظ البيانات: {e}")
    
    def add_channel(self, channel_id, channel_name, content_type, content_data):
        """إضافة قناة جديدة"""
        self.data[channel_id] = {
            'name': channel_name,
            'content_type': content_type,
            'content_data': content_data,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        self.save_data()
        print(f"✅ تمت إضافة القناة: {channel_name}")
    
    def update_channel(self, channel_id, content_type=None, content_data=None):
        """تحديث قناة موجودة"""
        if channel_id in self.data:
            if content_type:
                self.data[channel_id]['content_type'] = content_type
            if content_data:
                self.data[channel_id]['content_data'] = content_data
            self.data[channel_id]['updated_at'] = datetime.now().isoformat()
            self.save_data()
            print(f"✅ تم تحديث القناة: {self.data[channel_id]['name']}")
            return True
        return False
    
    def delete_channel(self, channel_id):
        """حذف قناة"""
        if channel_id in self.data:
            channel_name = self.data[channel_id]['name']
            del self.data[channel_id]
            self.save_data()
            print(f"✅ تم حذف القناة: {channel_name}")
            return True
        return False
    
    def get_channel(self, channel_id):
        """الحصول على بيانات قناة معينة"""
        return self.data.get(channel_id, {})
    
    def list_channels(self):
        """عرض كل القنوات"""
        print("\n📋 **قائمة القنوات المعدة:**")
        print("=" * 50)
        
        if not self.data:
            print("❌ لا توجد قنوات معدلة حالياً")
            return
        
        for channel_id, channel_data in self.data.items():
            print(f"\n📁 **{channel_data['name']}**")
            print(f"   🔹 المعرف: {channel_id}")
            print(f"   🔹 النوع: {channel_data['content_type']}")
            print(f"   🔹 آخر تحديث: {channel_data['updated_at']}")
    
    def create_sample_content(self):
        """إنشاء محتوى نموذجي"""
        sample_channels = [
            {
                'id': 'rules_channel_123',
                'name': 'قوانين',
                'content_type': 'rules',
                'content_data': {
                    'title': '🎮 **قوانين السيرفر** 🎮',
                    'description': 'يرجى الالتزام بالقوانين التالية:',
                    'rules': [
                        '📜 احترام جميع الأعضاء',
                        '📜 ممنوع إرسال روابط غير لائقة',
                        '📜 لا تكرار الرسائل',
                        '📜 استخدام اللغة اللائقة فقط',
                        '📜 عدم نشر معلومات شخصية'
                    ],
                    'color': 5814783,
                    'image': 'https://i.imgur.com/3D-rules-example.png'
                }
            },
            {
                'id': 'welcome_channel_456',
                'name': 'ترحيب',
                'content_type': 'welcome',
                'content_data': {
                    'title': '🎉 **أهلاً وسهلاً** 🎉',
                    'description': 'أهلاً بك في سيرفرنا!',
                    'messages': [
                        '🎊 نتمنى لك وقتاً ممتعاً',
                        '🌟 لا تتردد في المشاركة',
                        '🎮 شارك في الأنشطة والفعاليات'
                    ],
                    'color': 65280,
                    'image': 'https://i.imgur.com/welcome-example.png'
                }
            },
            {
                'id': 'announcement_channel_789',
                'name': 'إعلانات',
                'content_type': 'announcement',
                'content_data': {
                    'title': '📢 **إعلان هام** 📢',
                    'description': 'إعلان مهم لجميع الأعضاء',
                    'announcements': [
                        '📌 تابع القوانين دائماً',
                        '🎮 شارك في الفعاليات الأسبوعية',
                        '🏆 فرصة للفوز بجوائز قيمة'
                    ],
                    'color': 15158332,
                    'image': 'https://i.imgur.com/announcement-example.png'
                }
            }
        ]
        
        for channel in sample_channels:
            self.add_channel(
                channel['id'],
                channel['name'],
                channel['content_type'],
                channel['content_data']
            )
    
    def export_to_json(self, filename=None):
        """تصدير البيانات لملف JSON"""
        if not filename:
            filename = f"channels_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
            print(f"✅ تم تصدير البيانات إلى: {filename}")
        except Exception as e:
            print(f"❌ خطأ في التصدير: {e}")
    
    def import_from_json(self, filename):
        """استيراد البيانات من ملف JSON"""
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                imported_data = json.load(f)
            
            self.data.update(imported_data)
            self.save_data()
            print(f"✅ تم استيراد البيانات من: {filename}")
        except Exception as e:
            print(f"❌ خطأ في الاستيراد: {e}")

def main():
    """الواجهة الرئيسية لإدارة المحتوى"""
    manager = ContentManager()
    
    while True:
        print("\n🤖 **مدير محتوى بوت ديسكورد** 🤖")
        print("=" * 40)
        print("1. 📋 عرض كل القنوات")
        print("2. ➕ إضافة قناة جديدة")
        print("3. ✏️ تعديل قناة موجودة")
        print("4. 🗑️ حذف قناة")
        print("5. 📄 إنشاء محتوى نموذجي")
        print("6. 💾 تصدير البيانات")
        print("7. 📥 استيراد البيانات")
        print("8. ❌ خروج")
        print("=" * 40)
        
        choice = input("اختر رقم العملية: ").strip()
        
        if choice == '1':
            manager.list_channels()
        
        elif choice == '2':
            channel_id = input("معرف القناة: ").strip()
            channel_name = input("اسم القناة: ").strip()
            print("\nأنواع المحتوى المتاحة:")
            print("- rules (قوانين)")
            print("- welcome (ترحيب)")
            print("- announcement (إعلانات)")
            print("- text (نص عادي)")
            content_type = input("نوع المحتوى: ").strip().lower()
            
            # هنا يمكن إضافة واجهة لإنشاء المحتوى المخصص
            content_data = {}  # بيانات افتراضية
            
            manager.add_channel(channel_id, channel_name, content_type, content_data)
        
        elif choice == '3':
            channel_id = input("معرف القناة المراد تعديلها: ").strip()
            if manager.get_channel(channel_id):
                print("\nماذا تريد تعديله؟")
                print("1. نوع المحتوى")
                print("2. بيانات المحتوى")
                print("3. كل شيء")
                sub_choice = input("اختر: ").strip()
                
                if sub_choice in ['1', '3']:
                    content_type = input("النوع الجديد: ").strip().lower()
                else:
                    content_type = None
                
                if sub_choice in ['2', '3']:
                    # هنا يمكن إضافة واجهة لتعديل المحتوى
                    content_data = {}  # بيانات افتراضية
                else:
                    content_data = None
                
                manager.update_channel(channel_id, content_type, content_data)
            else:
                print("❌ القناة غير موجودة")
        
        elif choice == '4':
            channel_id = input("معرف القناة المراد حذفها: ").strip()
            if not manager.delete_channel(channel_id):
                print("❌ القناة غير موجودة")
        
        elif choice == '5':
            manager.create_sample_content()
        
        elif choice == '6':
            filename = input("اسم الملف (اختياري): ").strip()
            manager.export_to_json(filename if filename else None)
        
        elif choice == '7':
            filename = input("اسم الملف المستورد: ").strip()
            manager.import_from_json(filename)
        
        elif choice == '8':
            print("👋 وداعاً!")
            break
        
        else:
            print("❌ اختيار غير صالح، حاول مرة أخرى")

if __name__ == "__main__":
    main()
