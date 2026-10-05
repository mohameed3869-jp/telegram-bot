import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
from datetime import datetime

TOKEN = os.environ.get("TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "مرحباً بك في البوت!\n\n"
        "الأوامر المتاحة:\n"
        "/start - بدء البوت\n"
        "/help - المساعدة\n"
        "/time - الوقت الحالي\n"
        "/info - معلومات عنك"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "هذا بوت بسيط.\n"
        "تقدر ترسل أي رسالة وأرد عليك، أو تستخدم الأوامر."
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

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(f"أنت قلت: {update.message.text}")

def main():
    if not TOKEN:
        print("خطأ: التوكن غير موجود")
        return

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("time", time_command))
    app.add_handler(CommandHandler("info", info_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))

    print("البوت يعمل...")
    app.run_polling()

if __name__ == "__main__":
    main()