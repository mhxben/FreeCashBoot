# bot.py – نسخة متوافقة مع python-telegram-bot v20+
from email.mime import application
import logging
import json
from multiprocessing import context
import os
import random
from datetime import datetime, timedelta, date

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application, CommandHandler, CallbackQueryHandler,
    MessageHandler, filters, ContextTypes
)
TOKEN = "8202782331:AAGsuILUcFTg1Pli8344YIuUSOPm25XFyZo"
ADMIN_IDS = [5572616015 , 6897560789]
MIN_WITHDRAWAL = 5.0
REFERRAL_BONUS = 0.1
ANSWER_REWARD = 0.1
MAX_DAILY_QUESTIONS = 3
DB_FILE = "bot_database.json"

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)

logger = logging.getLogger(__name__)

# -------------------- قاعدة البيانات ------------------
async def handle_answer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user = query.from_user
    data = query.data  # الشكل: ans_رقم_الاختيار

    try:
        _, q_index, selected = data.split("_")
        q_index = int(q_index)
        selected = int(selected)
    except Exception as e:
        await query.edit_message_text("⚠️ حدث خطأ في تحليل الإجابة.")
        return

    db = load_db()
    questions = db["questions"]
    if q_index >= len(questions):
        await query.edit_message_text("⚠️ السؤال غير موجود.")
        return

    question = questions[q_index]
    correct_index = question["correct"]
    is_correct = selected == correct_index

    user_data = get_user(user.id)
    today = str(date.today())
    daily_answers = user_data.get("daily_answers", {}).get(today, 0)

    if is_correct:
        user_data["balance"] += ANSWER_REWARD
        user_data["answered_questions"].append(question["q"])
        user_data["daily_answers"][today] = daily_answers + 1
        update_user(user.id, user_data)
        message = "✅ إجابة صحيحة! حصلت على 0.1$"
    else:
        user_data["daily_answers"][today] = daily_answers + 1
        update_user(user.id, user_data)
        correct_choice = question["choices"][correct_index]
        message = f"❌ إجابة خاطئة!\nالإجابة الصحيحة هي: {correct_choice}"

    keyboard = []
    if user_data["daily_answers"][today] < MAX_DAILY_QUESTIONS:
        keyboard.append([InlineKeyboardButton("➡️ التالي", callback_data='questions')])
    else:
        keyboard.append([InlineKeyboardButton("📅 رجوع", callback_data='back')])

    await query.edit_message_text(message, reply_markup=InlineKeyboardMarkup(keyboard))

# -- الأسئلة --------------------
def init_db():
    if not os.path.exists(DB_FILE):
        questions = [
            {"q": "ما هي عاصمة فرنسا؟", "choices": ["باريس", "ميونخ", "بوردو", "مادريد"], "correct": 0},
            {"q": "كم عدد كواكب المجموعة الشمسية؟", "choices": ["7", "8", "9", "6"], "correct": 1},
            {"q": "من مؤسس شركة مايكروسوفت؟", "choices": ["بيل جيتس", "ستيف جوبز", "مارك", "لينكس"], "correct": 0},
            {"q": "أكبر كوكب؟", "choices": ["زحل", "الأرض", "المشتري", "نبتون"], "correct": 2},
            {"q": "أصغر كوكب؟", "choices": ["عطارد", "الزهرة", "القمر", "بلوتو"], "correct": 0},
            {"q": "سنة إطلاق فيسبوك؟", "choices": ["2004", "2003", "2005", "2006"], "correct": 0},
            {"q": "عدد قارات العالم؟", "choices": ["5", "6", "7", "8"], "correct": 2},
            {"q": "أطول نهر في العالم؟", "choices": ["النيل", "الأمازون", "الدانوب", "الفرات"], "correct": 1},
            {"q": "أكبر محيط؟", "choices": ["الأطلسي", "الهادئ", "الهندي", "القوقاز"], "correct": 1},
            {"q": "كم عدد أيام السنة؟", "choices": ["364", "365", "366", "360"], "correct": 1},
            {"q": "ما وحدة قياس الوقت؟", "choices": ["متر", "ثانية", "كيلو", "نيوتن"], "correct": 1},
            {"q": "أول من مشى على القمر؟", "choices": ["غاغارين", "أرمسترونغ", "ألدرين", "كولومبس"], "correct": 1},
            {"q": "ما عاصمة اليابان؟", "choices": ["كيوتو", "طوكيو", "أوساكا", "هيروشيما"], "correct": 1},
            {"q": "كم عدد أسنان الإنسان؟", "choices": ["28", "30", "32", "34"], "correct": 2},
            {"q": "ما لون الشمس؟", "choices": ["أصفر", "أبيض", "أحمر", "برتقالي"], "correct": 1},
            {"q": "أقرب كوكب للشمس؟", "choices": ["الزهرة", "عطارد", "الأرض", "المريخ"], "correct": 1},
            {"q": "أكبر صحراء؟", "choices": ["ساهارا", "أركتيك", "عربية", "كالاهاري"], "correct": 1},
            {"q": "عدد عظام جسم الإنسان؟", "choices": ["206", "216", "196", "236"], "correct": 0}
        ]
        save_db({"users": {}, "withdrawals": [], "questions": questions})

def load_db():
    with open(DB_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_db(data):
    with open(DB_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# -------------------- وظائف مساعدة --------------------
def get_user(uid, username=None):
    data = load_db()
    uid = str(uid)
    today = str(date.today())
    
    if uid not in data["users"]:
        data["users"][uid] = {
            "username": username,
            "balance": 0.0,
            "joined": today,
            "referrer": None,
            "answered_questions": [],
            "daily_answers": {today: 0}
        }
    else:
        if username:  # ✅ تحديث الاسم في حال تغيّر
            data["users"][uid]["username"] = username

    if today not in data["users"][uid].get("daily_answers", {}):
        data["users"][uid]["daily_answers"][today] = 0

    save_db(data)
    return data["users"][uid]


def update_user(uid, new_data):
    data = load_db()
    uid = str(uid)
    data["users"][uid] = new_data
    save_db(data)


# تابع سحب الرصيد عند الضغط على زر "سحب"
async def handle_withdraw_request(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    user_data = get_user(user_id)

    if user_data["balance"] >= MIN_WITHDRAWAL:
        context.user_data["awaiting_withdraw_amount"] = True
        await query.edit_message_text(
            f"📥 كم المبلغ الذي تريد سحبه؟ (بالدولار)\n💰 رصيدك الحالي: {user_data['balance']:.2f}$"
        )
    else:
        await query.edit_message_text("❌ الحد الأدنى للسحب هو 5$.\nرصيدك الحالي لا يكفي.")



# استقبال معرف محفظة Binance من المستخدم
# استقبال معرف محفظة Binance من المستخدم
async def handle_binance_id(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.from_user.id in ADMIN_IDS and context.user_data.get("awaiting_balance_add"):
        return
    user = update.message.from_user
    user_data = get_user(user.id)

    # إذا ننتظر المبلغ
    if context.user_data.get("awaiting_withdraw_amount"):
        try:
            amount = float(update.message.text)
        except ValueError:
            await update.message.reply_text("❌ من فضلك أرسل مبلغًا صالحًا (رقم).")
            return

        if amount < MIN_WITHDRAWAL or amount > user_data["balance"]:
            await update.message.reply_text("❌ المبلغ غير مسموح. تحقق من رصيدك وحد السحب.")
            return

        context.user_data["withdraw_amount"] = amount
        context.user_data["awaiting_withdraw_amount"] = False
        context.user_data["awaiting_binance_id"] = True

        await update.message.reply_text("✅ الآن، أرسل Binance ID الخاص بك:")
        return

    # إذا ننتظر Binance ID
    if context.user_data.get("awaiting_binance_id"):
        context.user_data["awaiting_binance_id"] = False
        binance_id = update.message.text
        amount = context.user_data.get("withdraw_amount", 0.0)

        # تحديث الرصيد
        user_data["balance"] -= amount
        update_user(user.id, user_data)

        await update.message.reply_text("✅ تم إرسال طلب السحب إلى الأدمن.")

        for admin_id in ADMIN_IDS:
            await context.bot.send_message(
                chat_id=admin_id,
                text=(
                    f"📥 طلب سحب جديد:\n\n"
                    f"👤 المستخدم: @{user.username or 'غير متوفر'}\n"
                    f"🆔 ID: {user.id}\n"
                    f"💰 المبلغ: {amount:.2f} $\n"
                    f"🏦 Binance ID: {binance_id}"
                )
            )
async def handle_referral(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    link = f"https://t.me/{context.bot.username}?start={query.from_user.id}"
    await query.edit_message_text(
        f"📨 رابط الدعوة الخاص بك:\n{link}",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
        ])
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_data = get_user(user.id, user.username)

    text = (
        f"مرحباً {user.first_name}!\n"
        "👥 كل صديق تدعوه يحصل على 0.1$\n"
        "❓ كل إجابة صحيحة على سؤال تحصل على 0.1$ (5 أسئلة/يوم)\n"
        "💰 يمكنك سحب رصيدك عندما يصل إلى 5$"
    )

    keyboard = [
        [InlineKeyboardButton("🧠 ابدأ الإجابة", callback_data="questions")],
        [InlineKeyboardButton("💰 رصيدي", callback_data="balance")],
        [InlineKeyboardButton("💸 سحب", callback_data="withdraw")],
        [InlineKeyboardButton("📨 دعوة صديق", callback_data="referral")]
        ]
    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard))



async def handle_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    user_data = get_user(query.from_user.id)

    balance = user_data["balance"]
    referrals = sum(1 for u in load_db()["users"].values() if u.get("referrer") == str(query.from_user.id))
    correct = len(user_data["answered_questions"])
    today = str(date.today())
    daily = user_data.get("daily_answers", {}).get(today, 0)

    text = (
        f"💰 رصيدك الحالي: {balance}$\n\n"
        f"👥 الأصدقاء المدعوين: {referrals}\n"
        f"💸 أرباح الدعوة: {referrals * REFERRAL_BONUS}$\n"
        f"💵 الإجابات الصحيحة: {correct}\n"
        f"📅 إجاباتك اليوم: {daily}/{MAX_DAILY_QUESTIONS}"
    )
    await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع", callback_data="back")]
    ]))

async def list_users_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.effective_message.reply_text("❌ ليس لديك صلاحية تنفيذ هذا الأمر.")
        return

    db = load_db()
    users = db.get("users", {})
    if not users:
        await update.effective_message.reply_text("لا يوجد مستخدمون.")
        return

    text = "📋 قائمة المستخدمين:\n\n"
    for uid, data in users.items():
        username = data.get("username") or "غير متوفر"
        balance = data.get("balance", 0.0)
        text += f"🆔 {uid} – @{username} – 💰 {balance}$\n"

    for part in split_message(text):
        await update.effective_message.reply_text(part)


async def handle_back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🧠 ابدأ الإجابة", callback_data="questions")],
        [InlineKeyboardButton("💰 رصيدي", callback_data="balance")],
        [InlineKeyboardButton("💸 سحب", callback_data="withdraw")],
        [InlineKeyboardButton("📨 دعوة صديق", callback_data="referral")]
    ]
    await update.callback_query.edit_message_text(
        "👋 أهلاً بك من جديد! اختر من الخيارات:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_questions(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    db = load_db()
    questions = db["questions"]
    user_data = get_user(query.from_user.id)

    today = str(date.today())
    daily_answers = user_data.get("daily_answers", {}).get(today, 0)

    if daily_answers >= MAX_DAILY_QUESTIONS:
        await query.edit_message_text("✅ لقد أجبت على الحد الأقصى من الأسئلة اليوم.")
        return

    unanswered = [q for q in questions if q["q"] not in user_data["answered_questions"]]
    if not unanswered:
        await query.edit_message_text("✅ لقد أجبت على جميع الأسئلة.")
        return

    question = random.choice(unanswered)
    index = questions.index(question)

    buttons = []
    for i, choice in enumerate(question["choices"]):
        buttons.append([InlineKeyboardButton(choice, callback_data=f"ans_{index}_{i}")])

    await query.edit_message_text(f"🧠 {question['q']}", reply_markup=InlineKeyboardMarkup(buttons))

async def add_balance_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id not in ADMIN_IDS:
        await update.message.reply_text("❌ ليس لديك صلاحية تنفيذ هذا الأمر.")
        return

    context.user_data["awaiting_balance_add"] = True
    await update.message.reply_text("📥 أرسل البيانات بهذا الشكل:\n`user_id amount`\nمثال:\n`123456789 5.0`")

async def handle_admin_input(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.user_data.get("awaiting_balance_add"):
        try:
            parts = update.message.text.split()
            uid = int(parts[0])
            amount = float(parts[1])
        except (IndexError, ValueError):
            await update.message.reply_text("⚠️ صيغة غير صحيحة. أرسل: `user_id amount`")
            return

        user_data = get_user(uid)
        user_data["balance"] += amount
        update_user(uid, user_data)

        context.user_data["awaiting_balance_add"] = False
        await update.message.reply_text(f"✅ تم إضافة {amount}$ للمستخدم {uid}.")
    # منع التعارض لاحقاً
    context.user_data["awaiting_binance_id"] = False
    context.user_data["awaiting_withdraw_amount"] = False


import asyncio
async def main():
    init_db()

    application = Application.builder().token(TOKEN).build()

    application.add_handler(CallbackQueryHandler(handle_answer, pattern="^ans_"))
    application.add_handler(CallbackQueryHandler(handle_withdraw_request, pattern="^withdraw$"))
    application.add_handler(CallbackQueryHandler(handle_questions, pattern="^questions$"))
    application.add_handler(CallbackQueryHandler(handle_balance, pattern="^balance$"))
    application.add_handler(CallbackQueryHandler(handle_back, pattern="^back$"))
    application.add_handler(CommandHandler("start", start_command))
    application.add_handler(CallbackQueryHandler(handle_referral, pattern="^referral$"))
    application.add_handler(CommandHandler("add_balance", add_balance_command))
    # فقط للأدمن: handle_admin_input
    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.User(user_id=ADMIN_IDS),
            handle_admin_input
        )
    )

    # لباقي المستخدمين: handle_binance_id
    application.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND & ~filters.User(user_id=ADMIN_IDS),
            handle_binance_id
        )
    )
    application.add_handler(CommandHandler("list_users", list_users_command))

    await application.run_polling()

import nest_asyncio

if __name__ == "__main__":
    nest_asyncio.apply()

    asyncio.run(main())

