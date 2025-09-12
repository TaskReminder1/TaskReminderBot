# database.py
import sqlite3
from datetime import datetime

DB_NAME = "task_reminder.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reminders (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            text TEXT NOT NULL,
            reminder_time TEXT NOT NULL,
            is_done BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            title TEXT,
            content TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            is_completed BOOLEAN DEFAULT 0
        )
    ''')

    conn.commit()
    conn.close()

def add_reminder(user_id, text, reminder_time):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO reminders (user_id, text, reminder_time)
        VALUES (?, ?, ?)
    ''', (user_id, text, reminder_time))
    reminder_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return reminder_id

def get_reminders(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, text, reminder_time, is_done, created_at
        FROM reminders WHERE user_id = ? ORDER BY reminder_time ASC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def delete_reminder(reminder_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM reminders WHERE id = ?', (reminder_id,))
    conn.commit()
    conn.close()

def mark_reminder_done(reminder_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('UPDATE reminders SET is_done = 1 WHERE id = ?', (reminder_id,))
    conn.commit()
    conn.close()

def add_note(user_id, title, content):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO notes (user_id, title, content)
        VALUES (?, ?, ?)
    ''', (user_id, title, content))
    note_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return note_id

def get_notes(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT id, title, content, is_completed, created_at
        FROM notes WHERE user_id = ? ORDER BY created_at DESC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def toggle_note_completion(note_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('SELECT is_completed FROM notes WHERE id = ?', (note_id,))
    current = cursor.fetchone()[0]
    new_status = 0 if current else 1
    cursor.execute('UPDATE notes SET is_completed = ? WHERE id = ?', (new_status, note_id))
    conn.commit()
    conn.close()

def delete_note(note_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('DELETE FROM notes WHERE id = ?', (note_id,))
    conn.commit()
    conn.close()
def add_habit(user_id, habit_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO habits (user_id, habit_name, total_days, current_streak)
        VALUES (?, ?, 0, 0)
    ''', (user_id, habit_name))
    conn.commit()
    conn.close()

def get_habits(user_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT habit_name, total_days, current_streak
        FROM habits WHERE user_id = ? ORDER BY habit_name ASC
    ''', (user_id,))
    rows = cursor.fetchall()
    conn.close()
    return rows

def mark_habit_done(user_id, habit_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    # Увеличиваем текущую полосу
    cursor.execute('''
        UPDATE habits 
        SET current_streak = current_streak + 1, 
            total_days = total_days + 1 
        WHERE user_id = ? AND habit_name = ?
    ''', (user_id, habit_name))
    # Получаем новое значение streak
    cursor.execute('''
        SELECT current_streak 
        FROM habits 
        WHERE user_id = ? AND habit_name = ?
    ''', (user_id, habit_name))
    new_streak = cursor.fetchone()[0]
    conn.commit()
    conn.close()
    return new_streak

def get_habit_streak(user_id, habit_name):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        SELECT current_streak 
        FROM habits 
        WHERE user_id = ? AND habit_name = ?
    ''', (user_id, habit_name))
    result = cursor.fetchone()
    conn.close()
    return result[0] if result else 0