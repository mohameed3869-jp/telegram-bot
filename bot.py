import os
import random
import tempfile
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime
import yt_dlp

TOKEN = os.environ.get("TOKEN")

# المواقع المدعومة
SUPPORTED_SITES = ["youtube.com", "youtu.be", "tiktok.com", "twitter.com", "x.com"]

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً بك في بوت التحميل!\n\n"
        "الأوامر المتاحة:\n"
        "/start - بدء البوت\n"
        "/help - المساعدة\n"
        "/time - الوقت الحالي\n"
        "/info - معلومات عنك\n"
        "/ping - فحص البوت\n\n"
        "أرسل رابط فيديو من:\n"
        "• يوتيوب\n"
        "• تيك توك\n"
        "• تويتر / X\n"
        "وأحمله لك بأعلى جودة ممكنة."
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "كيف تستخدم البوت:\n\n"
        "1. انسخ رابط الفيديو من يوتيوب أو تيك توك أو تويتر\n"
        "2. أرسل الرابط هنا\n"
        "3. انتظر شوي والبوت راح يرسلك الفيديو\n\n"
        "ملاحظة: الفيديوهات الكبيرة جداً ممكن ما تنرسل بسبب حدود تليجرام."
    )

async def time_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    await update.message.reply_text(f"الوقت الحالي: {now}")

async def info_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"معلوماتك:\n"
        f"الاسم: {user.first_name}\n"
        f"اليوزر: @{user.username if user.username else 'ما فيه'}\n"
        f"الآيدي: {user.id}"
    )

async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("البوت شغال 100% ⚡")

def is_supported_url(text: str) -> bool:
    text = text.lower()
    return any(site in text for site in SUPPORTED_SITES)

def download_video(url: str) -> str | None:
    """يحمل الفيديو ويرجع مسار الملف"""
    try:
        temp_dir = tempfile.gettempdir()
        output_template = os.path.join(temp_dir, "%(id)s.%(ext)s")

        ydl_opts = {
            "format": "best[ext=mp4]/best",  # أفضل جودة mp4
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "max_filesize": 49 * 1024 * 1024,  # تقريباً 49 ميجا (حد تليجرام)
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            return filename
    except Exception as e:
        print(f"خطأ في التحميل: {e}")
        return None

async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = update.message.text.strip()

    if not is_supported_url(url):
        await update.message.reply_text("هذا الرابط مو مدعوم. أرسل رابط من يوتيوب أو تيك توك أو تويتر فقط.")
        return

    await update.message.reply_text("جاري التحميل... انتظر قليلاً ⏳")

    # تشغيل التحميل في خيط منفصل عشان ما يوقف البوت
    loop = asyncio.get_event_loop()
    file_path = await loop.run_in_executor(None, download_video, url)

    if not file_path or not os.path.exists(file_path):
        await update.message.reply_text("فشل التحميل. جرب رابط ثاني أو تأكد إن الفيديو متاح.")
        return

    try:
        # إرسال الفيديو
        with open(file_path, "rb") as video:
            await update.message.reply_video(
                video=video,
                caption="تم التحميل بنجاح ✅",
                supports_streaming=True
            )
    except Exception as e:
        print(f"خطأ في الإرسال: {e}")
        # لو فشل كفيديو، نحاول نرسله كملف
        try:
            with open(file_path, "rb") as video:
                await update.message.reply_document(
                    document=video,
                    caption="تم التحميل (تم إرساله كملف)"
                )
        except Exception as e2:
            await update.message.reply_text("حجم الفيديو كبير جداً وما قدر يرسله تليجرام.")
    finally:
        # حذف الملف بعد الإرسال
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except:
            pass

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل رابط فيديو من يوتيوب أو تيك توك أو تويتر عشان أحمله لك.")

def main():
    if not TOKEN:
        print("خطأ: التوكن غير موجود")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("time", time_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("ping", ping))

    # أي رسالة فيها رابط مدعوم
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    print("البوت يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()
