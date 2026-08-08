

import sqlite3
import datetime
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
)

# Configuration
BOT_TOKEN = '8870516280:AAGaN9JD0tgRXV9ziV-X5E2INYJUkCrtZKw'

# Initialize Database
def init_db():
    conn = sqlite3.connect('irbo_tracker.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS study_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            username TEXT,
            hours REAL,
            category TEXT,
            notes TEXT,
            date TEXT,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# --- COMMAND HANDLERS ---

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    welcome_text = (
        "🧬 **IrBO 30 Tracker Bot** 🧬\n\n"
        "Commands:\n"
        "• `/log [hours] [category] [notes]` - Log study time\n"
        "  *Example:* `/log 3.5 campbell Solved 15 genetics problems`\n"
        "• `/leaderboard` - View weekly rankings\n"
        "• `/myreport` - View your total stats\n"
        "• `/help` - Show instructions"
    )
    await update.message.reply_text(welcome_text, parse_mode='Markdown')

async def log(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    username = user.first_name or user.username or "Anonymous"
    user_id = user.id
    
    if len(context.args) < 2:
        await update.message.reply_text("⚠️ Usage: `/log [hours] [category] [notes]`\nExample: `/log 2.5 genetics Solved 10 problems`", parse_mode='Markdown')
        return

    try:
        hours = float(context.args[0])
        category = context.args[1].lower()
        notes = " ".join(context.args[2:]) if len(context.args) > 2 else "No details"
        today = datetime.date.today().isoformat()

        conn = sqlite3.connect('irbo_tracker.db')
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO study_logs (user_id, username, hours, category, notes, date) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, username, hours, category, notes, today)
        )
        conn.commit()
        conn.close()

        await update.message.reply_text(f"✅ **Logged!**\n👤 {username}\n⏱️ {hours}h | 🏷️ {category.capitalize()}\n📝 {notes}", parse_mode='Markdown')
    except ValueError:
        await update.message.reply_text("⚠️ Please provide a valid number for hours. Example: `/log 3.5 campbell ...`", parse_mode='Markdown')

async def leaderboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Get start of the current week (Assuming Saturday start for Iranian schedule)
    today = datetime.date.today()
    # Find last Saturday (Python: Monday is 0, Sunday is 6, Saturday is 5)
    idx = (today.weekday() + 2) % 7
    saturday = today - datetime.timedelta(days=idx)
    sat_str = saturday.isoformat()

    conn = sqlite3.connect('irbo_tracker.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT username, SUM(hours) as total_hours 
        FROM study_logs 
        WHERE date >= ? 
        GROUP BY user_id 
        ORDER BY total_hours DESC
    ''', (sat_str,))
    rankings = cursor.fetchall()
    conn.close()

    if not rankings:
        await update.message.reply_text("📊 No logs recorded for this week yet!")
        return

    text = f"🏆 **IrBO 30 Weekly Leaderboard** (Since {sat_str}):\n\n"
    medals = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣", "6️⃣"]
    total_group_hours = 0

    for i, (name, hours) in enumerate(rankings):
        icon = medals[i] if i < len(medals) else "👤"
        text += f"{icon} **{name}**: {hours:.1f} hrs\n"
        total_group_hours += hours

    text += f"\n📈 **Group Total:** {total_group_hours:.1f} hrs"
    await update.message.reply_text(text, parse_mode='Markdown')

async def myreport(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    username = update.effective_user.first_name

    conn = sqlite3.connect('irbo_tracker.db')
    cursor = conn.cursor()
    
    # Total Hours
    cursor.execute("SELECT SUM(hours) FROM study_logs WHERE user_id = ?", (user_id,))
    total = cursor.fetchone()[0] or 0.0

    # Category Breakdown
    cursor.execute("SELECT category, SUM(hours) FROM study_logs WHERE user_id = ? GROUP BY category", (user_id,))
    breakdown = cursor.fetchall()
    conn.close()

    text = f"📊 **Personal Report: {username}**\n\n"
    text += f"⏱️ **Total All-Time Focus:** {total:.1f} hrs\n\n"
    text += "🏷️ **By Subject:**\n"
    for cat, hrs in breakdown:
        text += f"• {cat.capitalize()}: {hrs:.1f} hrs\n"

    await update.message.reply_text(text, parse_mode='Markdown')

# --- MAIN RUNNER ---

def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", start))
    app.add_handler(CommandHandler("log", log))
    app.add_handler(CommandHandler("leaderboard", leaderboard))
    app.add_handler(CommandHandler("myreport", myreport))

    print("Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()
