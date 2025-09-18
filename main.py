# main.py
import logging
import re
import asyncio
from datetime import datetime, timedelta
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackQueryHandler, ContextTypes, filters
from database import init_db, add_reminder, get_reminders, delete_reminder, mark_reminder_done, add_note, get_notes, toggle_note_completion, delete_note, add_habit, get_habits, mark_habit_done, get_habit_streak

# Включаем логирование
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

BOT_TOKEN = "8480651836:AAHGDJ84Yn3jMzbQJZ6cqx6leIVO-uqSZV4"  

# =====================
# ОБРАБОТЧИКИ КНОПОК
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await update.message.reply_text(
        f"👋 Привет, {user.first_name}!\n\n"
        "Я — твой персональный ассистент:\n"
        "🔹 Напомню о делах по времени\n"
        "🔹 Сохраню заметки и задачи\n"
        "🔹 Отслежу твои привычки и поддержу!\n\n"
        "Что хочешь сделать?",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⏰ Добавить напоминание", callback_data="add_reminder")],
            [InlineKeyboardButton("📝 Мои заметки", callback_data="show_notes")],
            [InlineKeyboardButton("🌱 Мои привычки", callback_data="show_habits")],
            [InlineKeyboardButton("📋 Мой список дел", callback_data="show_tasks")],
            [InlineKeyboardButton("💡 Помощь", callback_data="help")]
        ])
    )

async def add_reminder_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "📅 Отправь мне дату и время в формате:\n\n"
        "`ДД.ММ.ГГГГ ЧЧ:ММ`\n\n"
        "Например: `25.12.2024 18:30`\n\n"
        "Затем отправь текст напоминания (через новую строку)."
    )
    context.user_data['state'] = 'waiting_for_reminder_datetime'

async def add_note_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("✏️ Введи заголовок заметки:")
    context.user_data['state'] = 'waiting_for_note_title'

async def add_habit_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text("🌿 Какую привычку хочешь отслеживать? Например: «Пить воду», «Читать 10 страниц»\n\nНапиши название:")
    context.user_data['state'] = 'waiting_for_habit_name'

async def help_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(
        "💡 Помощь:\n\n"
        "• /remind — добавить напоминание\n"
        "• /notes — заметки и задачи\n"
        "• /habits — отслеживание привычек\n"
        "• Нажми на кнопки — они работают!\n\n"
        "Ты можешь помечать заметки как выполненные.\n"
        "Привычки отмечаются каждый день — я буду радоваться за тебя! ❤️",
        reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton("⬅️ Назад", callback_data="start")]])
    )

# =====================
# ОБРАБОТЧИКИ СООБЩЕНИЙ
# =====================

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    state = context.user_data.get('state')
    user_id = update.effective_user.id

    if state == 'waiting_for_reminder_datetime':
        text = update.message.text.strip()
        lines = text.splitlines()
        if len(lines) < 2:
            await update.message.reply_text("❌ Неверный формат. Пожалуйста, отправь:\n\n<дата и время>\n<текст напоминания>")
            return

        dt_str = lines[0].strip()
        reminder_text = "\n".join(lines[1:]).strip()

        pattern = r'^\d{2}\.\d{2}\.\d{4}\s\d{2}:\d{2}$'
        if not re.match(pattern, dt_str):
            await update.message.reply_text("❌ Неверный формат даты. Используй: `ДД.ММ.ГГГГ ЧЧ:ММ`")
            return

        try:
            reminder_time = datetime.strptime(dt_str, "%d.%m.%Y %H:%M")
            if reminder_time < datetime.now():
                await update.message.reply_text("❌ Нельзя ставить напоминание на прошлое!")
                return
        except ValueError:
            await update.message.reply_text("❌ Неверная дата или время.")
            return

        reminder_id = add_reminder(user_id, reminder_text, dt_str)
        await update.message.reply_text(
            f"✅ Напоминание сохранено!\n\n"
            f"⏰ {dt_str}\n"
            f"📝 {reminder_text}\n\n"
            f"Я напомню тебе!"
        )
        context.user_data['state'] = None

    elif state == 'waiting_for_note_title':
        context.user_data['note_title'] = update.message.text
        await update.message.reply_text("✏️ Теперь отправь содержание заметки:")
        context.user_data['state'] = 'waiting_for_note_content'

    elif state == 'waiting_for_note_content':
        title = context.user_data.get('note_title', '')
        content = update.message.text
        note_id = add_note(user_id, title, content)
        await update.message.reply_text(f"✅ Заметка сохранена!\n\n*{title}*\n{content}", parse_mode="Markdown")
        context.user_data['state'] = None
        context.user_data.pop('note_title', None)

    elif state == 'waiting_for_habit_name':
        habit_name = update.message.text.strip()
        if not habit_name:
            await update.message.reply_text("❌ Название не может быть пустым. Попробуй ещё раз:")
            return
        add_habit(user_id, habit_name)
        await update.message.reply_text(
            f"🎉 Отлично! Ты начал отслеживать привычку:\n\n*{habit_name}*\n\n"
            f"Каждый день, когда ты её выполнил — нажми кнопку «Отметить сегодня» 👇\n"
            f"Я буду считать твои успехи!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Отметить сегодня", callback_data=f"mark_habit_{habit_name}")]
            ])
        )
        context.user_data['state'] = None

# =====================
# ОБРАБОТЧИКИ КНОПОК (нажатия)
# =====================

async def handle_note_click(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data

    if data.startswith("note_"):
        note_id = int(data.split("_")[1])
        notes = get_notes(query.from_user.id)
        note = next((n for n in notes if n[0] == note_id), None)
        if note:
            note_id_db, title, content, is_completed, created_at = note
            status = "✅" if is_completed else "⬜"
            text = f"{status} *{title or 'Без названия'}*\n\n{content}\n\n_Создано: {created_at}_"
            keyboard = [
                [InlineKeyboardButton("🔄 Изменить статус", callback_data=f"toggle_{note_id}")],
                [InlineKeyboardButton("🗑 Удалить", callback_data=f"delete_note_{note_id}")],
                [InlineKeyboardButton("⬅️ Назад", callback_data="show_notes")]
            ]
            await query.edit_message_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

    elif data.startswith("toggle_"):
        note_id = int(data.split("_")[1])
        toggle_note_completion(note_id)
        await handle_note_click(update, context)

    elif data.startswith("delete_note_"):
        note_id = int(data.split("_")[2])
        delete_note(note_id)
        await show_notes(update, context)

    elif data == "show_notes":
        await show_notes(update, context)

    elif data == "show_habits":
        await show_habits(update, context)

    elif data == "show_tasks":
        await show_tasks(update, context)

    elif data == "add_reminder":
        await add_reminder_button(update, context)

    elif data == "add_note":
        await add_note_button(update, context)

    elif data == "add_habit":
        await add_habit_button(update, context)

    elif data == "help":
        await help_button(update, context)

    elif data == "start":
        await start(update, context)

    elif data.startswith("mark_habit_"):
        habit_name = data.replace("mark_habit_", "")
        user_id = update.effective_user.id
        streak = mark_habit_done(user_id, habit_name)
        await query.answer(f"🔥 Отмечено! Ты делаешь это уже {streak} дней подряд!", show_alert=True)
        await show_habits(update, context)

# =====================
# КОМАНДЫ
# =====================

async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📅 Отправь мне дату и время в формате:\n\n"
        "`ДД.ММ.ГГГГ ЧЧ:ММ`\n\n"
        "Например: `25.12.2024 18:30`\n\n"
        "Затем отправь текст напоминания (через новую строку)."
    )
    context.user_data['state'] = 'waiting_for_reminder_datetime'

async def notes_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_notes(update, context)

async def habits_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_habits(update, context)

async def tasks_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await show_tasks(update, context)

# =====================
# ПОКАЗАТЬ ЭЛЕМЕНТЫ
# =====================

async def show_notes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    notes = get_notes(user_id)
    if not notes:
        await update.message.reply_text("📭 У тебя пока нет заметок.", reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Добавить заметку", callback_data="add_note")]
        ]))
        return

    keyboard = []
    for note in notes:
        note_id, title, content, is_completed, _ = note
        btn_text = f"{'✅ ' if is_completed else '⬜ '} {title or 'Без названия'}"
        keyboard.append([InlineKeyboardButton(btn_text, callback_data=f"note_{note_id}")])

    keyboard.append([InlineKeyboardButton("➕ Добавить заметку", callback_data="add_note")])
    await update.message.reply_text("📝 *Твои заметки:*", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")

async def show_habits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    habits = get_habits(user_id)
    if not habits:
        await update.message.reply_text(
            "🌱 У тебя пока нет отслеживаемых привычек.\n\n"
            "Хочешь начать? Нажми кнопку ниже — и я помогу тебе стать лучше!",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("➕ Добавить привычку", callback_data="add_habit")]
            ])
        )
        return

    text = "🌿 *Твои привычки:*\n\n"
    for habit in habits:
        habit_name, total_days, current_streak = habit
        emoji = "🔥" if current_streak >= 7 else "💧" if current_streak >= 3 else "🌱"
        text += f"{emoji} *{habit_name}* — {total_days} дней ({current_streak} подряд)\n"

    text += "\n📌 Каждый день отмечай, что ты сделал — я буду радоваться за тебя!"

    await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Добавить привычку", callback_data="add_habit")]
    ]), parse_mode="Markdown")

async def show_tasks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "📋 Твой список дел — это твои заметки!\n\n"
        "Используй /notes, чтобы управлять ими.\n\n"
        "Также ты можешь помечать задачи как выполненные — просто нажми на них в меню.",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("📝 Мои заметки", callback_data="show_notes")]
        ])
    )

# =====================
# АВТОМАТИЧЕСКИЕ НАПОМИНАНИЯ (каждые 10 секунд проверяет)
# =====================

async def check_reminders(context: ContextTypes.DEFAULT_TYPE):
    now = datetime.now().strftime("%d.%m.%Y %H:%M")
    reminders = get_reminders(None)  # Получаем все напоминания

    for rem in reminders:
        rem_id, text, reminder_time, is_done, created_at = rem
        if is_done:
            continue
        if reminder_time <= now:
            # Отправляем напоминание
            user_id = rem[1]
            try:
                await context.bot.send_message(
                    chat_id=user_id,
                    text=f"⏰ *ВРЕМЯ!* \n\n{text}\n\nНе забудь — сейчас самое лучшее время для этого! 💪",
                    parse_mode="Markdown"
                )
                mark_reminder_done(rem_id)
                logger.info(f"Напоминание отправлено: {text} для пользователя {user_id}")
            except Exception as e:
                logger.error(f"Ошибка отправки напоминания: {e}")

# =====================
# ЗАПУСК БОТА
# =====================

def main():
    init_db()  # Инициализация базы данных

    app = Application.builder().token("8480651836:AAHGDJ84Yn3jMzbQJZ6cqx6leIVO-uqSZV4").build()

    # Команды
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("remind", remind_command))
    app.add_handler(CommandHandler("notes", notes_command))
    app.add_handler(CommandHandler("habits", habits_command))
    app.add_handler(CommandHandler("tasks", tasks_command))

    # Обработчики кнопок
    app.add_handler(CallbackQueryHandler(add_reminder_button, pattern="^add_reminder$"))
    app.add_handler(CallbackQueryHandler(add_note_button, pattern="^add_note$"))
    app.add_handler(CallbackQueryHandler(add_habit_button, pattern="^add_habit$"))
    app.add_handler(CallbackQueryHandler(help_button, pattern="^help$"))
    app.add_handler(CallbackQueryHandler(start, pattern="^start$"))

    app.add_handler(CallbackQueryHandler(handle_note_click, pattern=r"^(note_|toggle_|delete_note_|show_notes|show_habits|show_tasks|mark_habit_.+)$"))

    # Обработка текстовых сообщений
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Периодическая проверка напоминаний каждые 10 секунд
    job_queue = app.job_queue
    job_queue.run_repeating(check_reminders, interval=10, first=5)

    print("🚀 Бот запущен... (напоминания проверяются каждые 10 секунд)")
    app.run_polling()

if __name__ == '__main__':

    main()

