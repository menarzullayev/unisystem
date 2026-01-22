# D:\hemis_ai\bot_runner.py

import os
import django
import time
import schedule
import telebot
from datetime import timedelta
from django.utils import timezone
from threading import Thread
from django.db.models import Count
from dotenv import load_dotenv

# 1. ENV VA DJANGO MUHITINI SOZLASH
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
ENV_PATH = os.path.join(CURRENT_DIR, '.env')
load_dotenv(ENV_PATH)

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from core.models import User, EssayTopic, Attendance, Semester
from core.services import get_auth_token

# 2. BOT SOZLAMALARI
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

if not BOT_TOKEN:
    print("❌ XATOLIK: .env faylida TELEGRAM_BOT_TOKEN topilmadi!")
    exit(1)

bot = telebot.TeleBot(BOT_TOKEN)

# Foydalanuvchi ma'lumotlarini vaqtincha saqlash
user_data = {}

# Qayta-qayta xabar yubormaslik uchun kesh (Set)
sent_notifications = set()

print("🤖 Hemis AI Bot ishga tushdi (Dual Notification & Attendance Control)...")

# --- BOT HANDLERS ---

@bot.message_handler(commands=['start'])
def send_welcome(message):
    """1-QADAM: Start bosilganda Login so'raymiz"""
    msg = bot.reply_to(message, 
                 "Assalomu alaykum! Hemis AI botiga xush kelibsiz.\n\n"
                 "🆔 Iltimos, **Hemis loginingizni** (ID raqam) yuboring:")
    bot.register_next_step_handler(msg, process_login_step)

def process_login_step(message):
    """2-QADAM: Loginni qabul qilib, Parolni so'raymiz"""
    try:
        login_input = message.text.strip()
        chat_id = message.chat.id
        user_data[chat_id] = {'login': login_input}
        
        msg = bot.reply_to(message, f"✅ Login qabul qilindi: {login_input}\n\n🔑 Endi **Hemis parolingizni** yuboring:")
        bot.register_next_step_handler(msg, process_password_step)
    except Exception as e:
        bot.reply_to(message, "Xatolik yuz berdi. Iltimos /start buyrug'ini qayta bosing.")

def process_password_step(message):
    """3-QADAM: Parolni olib, tekshiramiz"""
    chat_id = message.chat.id
    try:
        password_input = message.text.strip()
        step_data = user_data.get(chat_id)
        
        if not step_data or 'login' not in step_data:
            bot.send_message(chat_id, "Jarayon buzildi. Iltimos /start ni qayta bosing.")
            return

        login_input = step_data['login']
        
        try:
            bot.delete_message(chat_id, message.message_id)
        except Exception:
            pass 

        bot.send_message(chat_id, "⏳ Tekshirilmoqda... (Parolingiz xavfsizlik uchun o'chirildi)")
        
        auth_resp = get_auth_token(login_input, password_input)
        
        if auth_resp['success']:
            try:
                user = User.objects.get(username=login_input)
                user.telegram_chat_id = str(chat_id)
                user.save()
                bot.send_message(chat_id, f"✅ Muvaffaqiyatli ulandiz, **{user.full_name}**!\n\n"
                                          "Endi sizga:\n"
                                          "1. Topshiriq muddati tugashiga 1 kun va 2 soat qolganda eslatma boradi.\n"
                                          "2. NB (qoldirilgan darslar) 5 taga yetsa ogohlantirish boradi.")
            except User.DoesNotExist:
                bot.send_message(chat_id, "❌ Siz avval Hemis AI saytiga kirishingiz kerak.")
        else:
            bot.send_message(chat_id, "❌ Login yoki parol noto'g'ri. /start ni bosing.")
        
        if chat_id in user_data: del user_data[chat_id]
            
    except Exception as e:
        bot.send_message(chat_id, f"Tizim xatoligi: {str(e)}")
        if chat_id in user_data: del user_data[chat_id]

# --- CRON JOB 1: DEDLAYNLAR (1 kun va 2 soat oldin) ---

def check_deadlines():
    print(f"⏳ [{timezone.now().strftime('%H:%M:%S')}] Dedlaynlar tekshirilmoqda...")
    now = timezone.now()
    
    upcoming_topics = EssayTopic.objects.filter(
        deadline__gt=now,
        deadline__lte=now + timedelta(hours=25)
    )
    
    if not upcoming_topics.exists():
        return

    connected_users = User.objects.filter(telegram_chat_id__isnull=False).exclude(telegram_chat_id='')

    for topic in upcoming_topics:
        time_left = topic.deadline - now
        hours_left = time_left.total_seconds() / 3600
        
        notification_type = None
        
        if 23.0 < hours_left <= 24.5:
            notification_type = "1_day"
            msg_header = "📅 ESALATMA: 1 kun qoldi!"
        elif 1.0 < hours_left <= 2.5:
            notification_type = "2_hours"
            msg_header = "🚨 SHOSHILINCH: 2 soat qoldi!"
            
        if not notification_type:
            continue

        for user in connected_users:
            cache_key = f"{user.id}:{topic.id}:{notification_type}"
            if cache_key in sent_notifications:
                continue
                
            if user.submissions.filter(topic=topic, status__in=['ai_graded', 'done', 'teacher_review']).exists():
                continue

            try:
                msg = (f"{msg_header}\n\n"
                       f"📚 Mavzu: {topic.title}\n"
                       f"⏳ Aniq vaqt qoldi: {int(hours_left)} soat {int((hours_left % 1)*60)} daqiqa\n"
                       f"⏰ Muddat: {topic.deadline.strftime('%d.%m.%Y %H:%M')}\n\n"
                       f"Iltimos, ishingizni yuklang!")
                
                bot.send_message(user.telegram_chat_id, msg)
                print(f"   -> Xabar ({notification_type}) yuborildi: {user.full_name}")
                sent_notifications.add(cache_key)
            except Exception as e:
                print(f"   -> Xatolik ({user.username}): {e}")

# --- CRON JOB 2: DAVOMAT (NB) NAZORATI ---

def check_attendance():
    print(f"🔍 [{timezone.now().strftime('%H:%M:%S')}] Davomat (NB) tekshirilmoqda...")
    
    current_sem = Semester.objects.filter(current=True).first()
    if not current_sem:
        return

    connected_users = User.objects.filter(telegram_chat_id__isnull=False).exclude(telegram_chat_id='')

    for user in connected_users:
        subject_stats = Attendance.objects.filter(
            user=user, 
            semester=current_sem
        ).values('subject__name', 'subject__id').annotate(nb_count=Count('id'))
        
        for stat in subject_stats:
            nb_count = stat['nb_count']
            subj_name = stat['subject__name']
            subj_id = stat['subject__id']
            
            if nb_count >= 5:
                cache_key = f"{user.id}:{subj_id}:nb_{nb_count}"
                
                if cache_key not in sent_notifications:
                    try:
                        msg = (f"⚠️ MUHIM OGOHLANTIRISH!\n\n"
                               f"Hurmatli {user.full_name},\n"
                               f"Sizning **'{subj_name}'** fanidan qoldirilgan darslaringiz (NB) soni **{nb_count}** taga yetdi!\n\n"
                               f"Iltimos, darslarga qatnashing yoki sababli hujjatlarni taqdim qiling.\n"
                               f"Aks holda yakuniy imtihonga kiritilmasligingiz mumkin.")
                        
                        bot.send_message(user.telegram_chat_id, msg)
                        print(f"   -> NB Ogohlantirish ({nb_count}): {user.full_name} -> {subj_name}")
                        sent_notifications.add(cache_key)
                    except Exception as e:
                        print(f"   -> Xatolik NB ({user.username}): {e}")

# Har soatda tekshirish
schedule.every().hour.do(check_deadlines)
schedule.every().hour.do(check_attendance)

# --- RUNNER ---

def run_schedule():
    while True:
        schedule.run_pending()
        time.sleep(60)

if __name__ == "__main__":
    t = Thread(target=run_schedule)
    t.start()
    
    print("🚀 Bot ishga tushdi va aloqa kuzatilmoqda...")
    
    while True:
        try:
            # Timeoutlarni oshiramiz va qayta ulanishni siklga olamiz
            bot.infinity_polling(timeout=60, long_polling_timeout=60)
        except Exception as e:
            print(f"⚠️ Bot aloqasi uzildi ({str(e)}). 5 soniyadan keyin qayta ulanadi...")
            time.sleep(5)