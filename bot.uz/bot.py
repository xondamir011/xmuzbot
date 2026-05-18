import os
import logging
from dotenv import load_dotenv

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    CallbackQueryHandler
)

from database import Database
from ai_checker import AIChecker

# .env faylni yuklash
load_dotenv()

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# .env dan olish
BOT_TOKEN = os.getenv("BOT_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")

db = Database("homework.db")
checker = AIChecker(ANTHROPIC_API_KEY)

ADMIN_IDS = [842135071]

# ─────────────────────────────────────────────
#  BUYRUQLAR
# ─────────────────────────────────────────────

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.register_user(user.id, user.full_name, user.username)
    
    keyboard = [
        [InlineKeyboardButton("📚 Uy ishini topshirish", callback_data="submit_hw")],
        [InlineKeyboardButton("🏆 Reyting ko'rish", callback_data="show_rating")],
        [InlineKeyboardButton("📋 Mening natijalarim", callback_data="my_results")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    await update.message.reply_text(
        f"👋 Salom, {user.first_name}!\n\n"
        "🤖 Men uy ishlarini tekshiruvchi botman.\n\n"
        "📝 Qanday ishlaydi:\n"
        "1. O'qituvchi vazifa beradi (/set_task)\n"
        "2. Sen uy ishingni yozib yuborsiz\n"
        "3. AI tekshiradi va ball beradi\n"
        "4. Reyting yangilanadi\n\n"
        "Tanlang:",
        reply_markup=reply_markup
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    is_admin = update.effective_user.id in ADMIN_IDS
    
    text = (
        "📖 *Bot buyruqlari:*\n\n"
        "*O'quvchilar uchun:*\n"
        "/start - Botni boshlash\n"
        "/submit - Uy ishini topshirish\n"
        "/rating - Umumiy reyting\n"
        "/myresults - Mening natijalarim\n"
        "/task - Joriy vazifani ko'rish\n\n"
    )
    
    if is_admin:
        text += (
            "*Admin buyruqlari:*\n"
            "/set_task [vazifa] - Yangi vazifa berish\n"
            "/set_prompt [prompt] - AI tekshirish promptini sozlash\n"
            "/results - Barcha natijalar\n"
            "/clear_task - Vazifani tozalash\n"
            "/add_admin [user_id] - Admin qo'shish\n"
        )
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ─────────────────────────────────────────────
#  ADMIN BUYRUQLARI
# ─────────────────────────────────────────────

async def set_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Bu buyruq faqat adminlar uchun!")
        return
    
    if not context.args:
        await update.message.reply_text(
            "❌ Vazifani kiriting!\n\n"
            "Misol: /set_task Pythonda ikki sonni qo'shuvchi funksiya yozing"
        )
        return
    
    task_text = " ".join(context.args)
    group_id = update.effective_chat.id
    db.set_task(group_id, task_text, update.effective_user.id)
    
    await update.message.reply_text(
        f"✅ *Yangi vazifa berildi!*\n\n"
        f"📝 {task_text}\n\n"
        f"O'quvchilar /submit buyrug'i orqali topshira oladi.",
        parse_mode='Markdown'
    )

async def set_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Bu buyruq faqat adminlar uchun!")
        return
    
    if not context.args:
        current_prompt = db.get_prompt(update.effective_chat.id)
        await update.message.reply_text(
            f"📋 *Joriy prompt:*\n\n{current_prompt}\n\n"
            "Yangi prompt qo'yish uchun: /set_prompt [yangi prompt]",
            parse_mode='Markdown'
        )
        return
    
    prompt_text = " ".join(context.args)
    db.set_prompt(update.effective_chat.id, prompt_text)
    await update.message.reply_text("✅ Prompt yangilandi!")

async def add_admin(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Bu buyruq faqat adminlar uchun!")
        return
    
    if not context.args:
        await update.message.reply_text("Foydalanish: /add_admin [user_id]")
        return
    
    try:
        new_admin_id = int(context.args[0])
        ADMIN_IDS.append(new_admin_id)
        await update.message.reply_text(f"✅ {new_admin_id} admin qilindi!")
    except ValueError:
        await update.message.reply_text("❌ Noto'g'ri user ID!")

async def show_all_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Bu buyruq faqat adminlar uchun!")
        return
    
    group_id = update.effective_chat.id
    results = db.get_all_results(group_id)
    
    if not results:
        await update.message.reply_text("📭 Hali hech kim topshirmagan.")
        return
    
    text = "📊 *Barcha natijalar:*\n\n"
    for i, r in enumerate(results, 1):
        text += f"{i}. {r['name']} — {r['score']}/100 ball\n"
        text += f"   📝 {r['feedback'][:50]}...\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def clear_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("❌ Bu buyruq faqat adminlar uchun!")
        return
    
    db.clear_task(update.effective_chat.id)
    await update.message.reply_text("🗑️ Vazifa tozalandi va natijalar arxivlandi.")

# ─────────────────────────────────────────────
#  O'QUVCHI BUYRUQLARI
# ─────────────────────────────────────────────

async def show_task(update: Update, context: ContextTypes.DEFAULT_TYPE):
    group_id = update.effective_chat.id
    task = db.get_current_task(group_id)
    
    if not task:
        await update.message.reply_text(
            "📭 Hozircha vazifa yo'q.\n"
            "O'qituvchingiz /set_task buyrug'i bilan vazifa beradi."
        )
        return
    
    await update.message.reply_text(
        f"📚 *Joriy vazifa:*\n\n{task['text']}\n\n"
        f"📅 Berilgan vaqt: {task['created_at']}\n\n"
        "✍️ Uy ishingizni topshirish uchun /submit yozing yoki "
        "«📚 Uy ishini topshirish» tugmasini bosing.",
        parse_mode='Markdown'
    )

async def submit_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    db.register_user(user.id, user.full_name, user.username)
    
    group_id = update.effective_chat.id
    task = db.get_current_task(group_id)
    
    if not task:
        await update.message.reply_text(
            "📭 Hozircha tekshiriladigan vazifa yo'q.\n"
            "O'qituvchingizdan vazifa berishini so'rang."
        )
        return
    
    # Foydalanuvchini kutish holatiga o'tkazish
    context.user_data['awaiting_homework'] = True
    context.user_data['task_id'] = task['id']
    context.user_data['group_id'] = group_id
    
    await update.message.reply_text(
        f"✍️ *Uy ishingizni yozing:*\n\n"
        f"📚 Vazifa: {task['text']}\n\n"
        f"Uy ishingizni quyida yozing yoki yuboring:",
        parse_mode='Markdown'
    )

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruhga kelgan xabarlarni qayta ishlash"""
    if not update.message or not update.message.text:
        return
    
    user = update.effective_user
    
    # Uy ishi kutilayotgan bo'lsa
    if context.user_data.get('awaiting_homework'):
        await process_homework(update, context)
        return

async def process_homework(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Uy ishini AI bilan tekshirish"""
    user = update.effective_user
    homework_text = update.message.text
    task_id = context.user_data.get('task_id')
    group_id = context.user_data.get('group_id', update.effective_chat.id)
    
    # Holatni tozalash
    context.user_data['awaiting_homework'] = False
    
    task = db.get_current_task(group_id)
    if not task:
        await update.message.reply_text("❌ Vazifa topilmadi.")
        return
    
    # Tekshirish xabari
    checking_msg = await update.message.reply_text(
        "⏳ Uy ishingiz tekshirilmoqda...\n🤖 AI baholayapti, biroz kuting..."
    )
    
    # AI prompt
    custom_prompt = db.get_prompt(group_id)
    
    try:
        result = await checker.check_homework(
            task=task['text'],
            homework=homework_text,
            student_name=user.full_name,
            custom_prompt=custom_prompt
        )
        
        # Natijani saqlash
        db.save_result(
            group_id=group_id,
            task_id=task['id'],
            user_id=user.id,
            homework_text=homework_text,
            score=result['score'],
            feedback=result['feedback'],
            strengths=result['strengths'],
            weaknesses=result['weaknesses']
        )
        
        # Reytingni yangilash
        db.update_rating(group_id, user.id, result['score'])
        
        # Natijani ko'rsatish
        score = result['score']
        emoji = "🥇" if score >= 90 else "🥈" if score >= 75 else "🥉" if score >= 60 else "📉"
        
        await checking_msg.edit_text(
            f"{emoji} *{user.full_name}* — {score}/100 ball\n\n"
            f"📝 *Baho:*\n{result['feedback']}\n\n"
            f"✅ *Yaxshi tomonlari:*\n{result['strengths']}\n\n"
            f"❗ *Kamchiliklar:*\n{result['weaknesses']}\n\n"
            f"🏆 Reytingni ko'rish: /rating",
            parse_mode='Markdown'
        )
        
    except Exception as e:
        logger.error(f"AI tekshirish xatosi: {e}")
        await checking_msg.edit_text(
            "❌ Tekshirishda xatolik yuz berdi. Qayta urinib ko'ring."
        )

async def show_rating(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Guruh reytingini ko'rsatish"""
    group_id = update.effective_chat.id
    ratings = db.get_rating(group_id)
    
    if not ratings:
        await update.message.reply_text(
            "📭 Hali reyting yo'q.\n"
            "Uy ishi topshirilganda reyting shakllanadi."
        )
        return
    
    medals = ["🥇", "🥈", "🥉"]
    text = "🏆 *REYTING JADVALI*\n" + "─" * 30 + "\n\n"
    
    for i, r in enumerate(ratings[:10], 1):
        medal = medals[i-1] if i <= 3 else f"{i}."
        bar = "█" * (r['avg_score'] // 10) + "░" * (10 - r['avg_score'] // 10)
        text += (
            f"{medal} *{r['name']}*\n"
            f"   {bar} {r['avg_score']:.1f}/100\n"
            f"   📝 {r['submissions']} ta uy ishi\n\n"
        )
    
    await update.message.reply_text(text, parse_mode='Markdown')

async def my_results(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Shaxsiy natijalar"""
    user = update.effective_user
    group_id = update.effective_chat.id
    results = db.get_user_results(group_id, user.id)
    
    if not results:
        await update.message.reply_text(
            "📭 Siz hali uy ishi topshirmagansiz.\n"
            "/submit buyrug'i bilan boshlang!"
        )
        return
    
    text = f"📊 *{user.full_name} — Natijalar*\n\n"
    
    total = sum(r['score'] for r in results)
    avg = total / len(results)
    
    text += f"📈 O'rtacha ball: *{avg:.1f}/100*\n"
    text += f"📝 Jami topshirgan: *{len(results)} ta*\n\n"
    text += "─" * 20 + "\n\n"
    
    for r in results[-5:]:  # Oxirgi 5 ta
        emoji = "✅" if r['score'] >= 70 else "⚠️"
        text += f"{emoji} Ball: {r['score']}/100\n"
        text += f"   🕐 {r['submitted_at']}\n\n"
    
    await update.message.reply_text(text, parse_mode='Markdown')

# ─────────────────────────────────────────────
#  CALLBACK HANDLER (Inline tugmalar)
# ─────────────────────────────────────────────

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    if query.data == "submit_hw":
        # submit_command ni simulatsiya qilish
        group_id = update.effective_chat.id
        task = db.get_current_task(group_id)
        
        if not task:
            await query.edit_message_text("📭 Hozircha tekshiriladigan vazifa yo'q.")
            return
        
        context.user_data['awaiting_homework'] = True
        context.user_data['task_id'] = task['id']
        context.user_data['group_id'] = group_id
        
        await query.edit_message_text(
            f"✍️ *Uy ishingizni yozing:*\n\n"
            f"📚 Vazifa: {task['text']}\n\n"
            "Uy ishingizni quyida yozing:",
            parse_mode='Markdown'
        )
    
    elif query.data == "show_rating":
        group_id = update.effective_chat.id
        ratings = db.get_rating(group_id)
        
        if not ratings:
            await query.edit_message_text("📭 Hali reyting yo'q.")
            return
        
        medals = ["🥇", "🥈", "🥉"]
        text = "🏆 *REYTING JADVALI*\n\n"
        
        for i, r in enumerate(ratings[:10], 1):
            medal = medals[i-1] if i <= 3 else f"{i}."
            text += f"{medal} *{r['name']}* — {r['avg_score']:.1f}/100 ({r['submissions']} ta)\n"
        
        keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="back_start")]]
        await query.edit_message_text(
            text, parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "my_results":
        user = update.effective_user
        group_id = update.effective_chat.id
        results = db.get_user_results(group_id, user.id)
        
        if not results:
            await query.edit_message_text(
                "📭 Siz hali uy ishi topshirmagansiz.\n/submit buyrug'i bilan boshlang!"
            )
            return
        
        avg = sum(r['score'] for r in results) / len(results)
        text = (
            f"📊 *Sizning natijalaringiz*\n\n"
            f"📈 O'rtacha: *{avg:.1f}/100*\n"
            f"📝 Topshirilgan: *{len(results)} ta*\n"
        )
        keyboard = [[InlineKeyboardButton("🔙 Orqaga", callback_data="back_start")]]
        await query.edit_message_text(
            text, parse_mode='Markdown',
            reply_markup=InlineKeyboardMarkup(keyboard)
        )
    
    elif query.data == "back_start":
        keyboard = [
            [InlineKeyboardButton("📚 Uy ishini topshirish", callback_data="submit_hw")],
            [InlineKeyboardButton("🏆 Reyting ko'rish", callback_data="show_rating")],
            [InlineKeyboardButton("📋 Mening natijalarim", callback_data="my_results")],
        ]
        await query.edit_message_text(
            "Asosiy menyu:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

# ─────────────────────────────────────────────
#  BOTNI ISHGA TUSHIRISH
# ─────────────────────────────────────────────

def main():
    db.init_db()
    
    app = Application.builder().token(BOT_TOKEN).build()
    
    # Buyruqlar
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("task", show_task))
    app.add_handler(CommandHandler("submit", submit_command))
    app.add_handler(CommandHandler("rating", show_rating))
    app.add_handler(CommandHandler("myresults", my_results))
    
    # Admin buyruqlari
    app.add_handler(CommandHandler("set_task", set_task))
    app.add_handler(CommandHandler("set_prompt", set_prompt))
    app.add_handler(CommandHandler("results", show_all_results))
    app.add_handler(CommandHandler("clear_task", clear_task))
    app.add_handler(CommandHandler("add_admin", add_admin))
    
    # Callback va xabar handlerlari
    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    
    print("🤖 Bot ishga tushdi!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()