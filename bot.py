import asyncio
import logging
import os
import tempfile
from datetime import datetime

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters
import yt_dlp

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

TOKEN = os.environ.get("TOKEN") or os.environ.get("TELEGRAM_TOKEN")
if not TOKEN:
    raise SystemExit("TOKEN env var is not set")

SUPPORTED_SITES = ["youtube.com", "youtu.be", "tiktok.com", "twitter.com", "x.com"]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً بك في بوت التحميل 🎬\n\n"
        "📌 الوصف:\n"
        "بوت متخصص في تحميل الفيديوهات من المواقع التالية:\n"
        "• يوتيوب\n"
        "• تيك توك\n"
        "• تويتر / X\n\n"
        "✨ طريقة الاستخدام:\n"
        "1. انسخ رابط الفيديو\n"
        "2. أرسله هنا\n"
        "3. انتظر قليلاً واستلم الفيديو بأعلى جودة متاحة\n\n"
        "⚠️ ملاحظات:\n"
        "- الفيديوهات الكبيرة جداً قد لا تُرسل بسبب حدود تليجرام\n"
        "- استخدم البوت بشكل مسؤول"
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
    text = text.lower().strip()
    return any(site in text for site in SUPPORTED_SITES)


def download_video(url: str):
    try:
        temp_dir = tempfile.mkdtemp(prefix="telegram_bot_")
        output_template = os.path.join(temp_dir, "%(title)s.%(ext)s")

        ydl_opts = {
            "format": "best[ext=mp4]/best",
            "outtmpl": output_template,
            "quiet": True,
            "no_warnings": True,
            "noplaylist": True,
            "max_filesize": 49 * 1024 * 1024,
            "socket_timeout": 30,
            "retries": 2,
        }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            if not info:
                return None

            file_path = info.get("_filename") or ydl.prepare_filename(info)
            if file_path and os.path.exists(file_path):
                return file_path

            for root, _, files in os.walk(temp_dir):
                for filename in files:
                    full_path = os.path.join(root, filename)
                    if os.path.isfile(full_path):
                        return full_path
            return None
    except yt_dlp.utils.DownloadError as exc:
        logger.error("فشل تحميل الفيديو: %s", exc)
        return None
    except Exception as exc:
        logger.exception("خطأ غير متوقع أثناء التحميل: %s", exc)
        return None


async def handle_url(update: Update, context: ContextTypes.DEFAULT_TYPE):
    url = (update.message.text or "").strip()

    if not url:
        return

    if not is_supported_url(url):
        await update.message.reply_text("هذا الرابط مو مدعوم. أرسل رابط من يوتيوب أو تيك توك أو تويتر فقط.")
        return

    await update.message.reply_text("جاري التحميل... انتظر قليلاً ⏳")

    file_path = await asyncio.to_thread(download_video, url)

    if not file_path or not os.path.exists(file_path):
        await update.message.reply_text("فشل التحميل. جرب رابط ثاني أو تأكد إن الفيديو متاح.")
        return

    try:
        with open(file_path, "rb") as video:
            await update.message.reply_video(
                video=video,
                caption="تم التحميل بنجاح ✅",
                supports_streaming=True,
            )
    except Exception as exc:
        logger.exception("خطأ في إرسال الفيديو: %s", exc)
        try:
            with open(file_path, "rb") as video:
                await update.message.reply_document(
                    document=video,
                    caption="تم التحميل (تم إرساله كملف)",
                )
        except Exception:
            await update.message.reply_text("حجم الفيديو كبير جداً وما قدر يرسله تليجرام.")
    finally:
        try:
            if os.path.exists(file_path):
                os.remove(file_path)
        except Exception:
            pass

        try:
            temp_dir = os.path.dirname(file_path)
            if temp_dir and os.path.isdir(temp_dir):
                for root, dirs, files in os.walk(temp_dir, topdown=False):
                    for filename in files:
                        try:
                            os.remove(os.path.join(root, filename))
                        except Exception:
                            pass
                    for directory in dirs:
                        try:
                            os.rmdir(os.path.join(root, directory))
                        except Exception:
                            pass
                try:
                    os.rmdir(temp_dir)
                except Exception:
                    pass
        except Exception:
            pass


async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("أرسل رابط فيديو من يوتيوب أو تيك توك أو تويتر عشان أحمله لك.")


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("time", time_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(CommandHandler("ping", ping))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_url))

    logger.info("البوت يعمل...")
    app.run_polling()


if __name__ == "__main__":
    main()
