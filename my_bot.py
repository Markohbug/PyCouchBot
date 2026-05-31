import logging
from dataclasses import dataclass
import os
from typing import Dict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    CallbackQueryHandler,
    ChatMemberHandler,
    MessageHandler,
    filters,
)

# 1. LOCAL LOGGING SETUP (Prints bot activity directly to your terminal screen)
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)

# --- 2. LOCAL DATA STORAGE LAYER ---
@dataclass
class UserProfile:
    user_id: int
    current_tier: int = 1
    current_lesson: int = 1
    points: int = 0

# Simple local dictionary serving as our data store
local_db: Dict[int, UserProfile] = {}

async def get_profile(user_id: int) -> UserProfile:
    """Helper function to fetch or initialize a user profile in memory."""
    if user_id not in local_db:
        local_db[user_id] = UserProfile(user_id=user_id)
        logger.info(f"Local DB: Initialized new profile for user {user_id}")
    return local_db[user_id]

# --- 3. STATE DEFINITIONS FOR THE BOT ENGINE ---
IDLE, IN_LESSON, IN_QUIZ = range(3)

# --- 4. INTERACTIVE KEYBOARDS ---
def get_syllabus_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [InlineKeyboardButton("⚙️ Tier 1: Python Server Core", callback_data="tier_1")],
        [InlineKeyboardButton("🌐 Tier 2: Networking & HTTP", callback_data="tier_2")],
        [InlineKeyboardButton("🗄️ Tier 3: Databases & ORMs", callback_data="tier_3")],
        [InlineKeyboardButton("🚀 Tier 4: System Architecture", callback_data="tier_4")],
    ]
    return InlineKeyboardMarkup(keyboard)

def get_quiz_keyboard() -> InlineKeyboardMarkup:
    keyboard = [
        [
            InlineKeyboardButton("[a] string", callback_data="quiz_wrong_string"),
            InlineKeyboardButton("[b] json", callback_data="quiz_correct"),
        ],
        [
            InlineKeyboardButton("[c] os", callback_data="quiz_wrong_os"),
            InlineKeyboardButton("[d] requests", callback_data="quiz_wrong_req"),
        ],
    ]
    return InlineKeyboardMarkup(keyboard)

# --- 5. COMMAND ACTIONS ---
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Triggered by /start. Greets the user and shows the learning tiers."""
    user = update.effective_user
    if not user:
        return ConversationHandler.END
    
    profile = await get_profile(user.id)
    
    welcome_text = (
        f"👋 *Welcome to the Backend Engineering Core, Engineer!* \n\n"
        f"I'm your automated Tech Lead. We aren't here to write basic loops; "
        f"we are here to build high-availability, low-latency, resilient systems.\n\n"
        f"Your local runtime profile is ready. Current Points: `{profile.points}` XP.\n"
        f"Choose a Tier from the Syllabus below to begin."
    )
    
    await update.message.reply_text(
        text=welcome_text, parse_mode="Markdown", reply_markup=get_syllabus_keyboard()
    )
    return IDLE

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Triggered by /status. Displays the user's progress variables."""
    user = update.effective_user
    if not user:
        return ConversationHandler.END
        
    profile = await get_profile(user.id)
    
    status_text = (
        f"📊 *LOCAL TELEMETRY RUNTIME METRICS:*\n"
        f"----------------------------------------\n"
        f"🏅 current_tier   :: Tier {profile.current_tier}\n"
        f"📖 current_lesson :: Lesson {profile.current_lesson}\n"
        f"⚡ learning_points:: {profile.points} XP\n"
        f"----------------------------------------\n"
        f"Status: *Local Development Environment Stable.*"
    )
    await update.message.reply_text(text=status_text, parse_mode="Markdown")
    return IDLE

# --- 6. CORE APP INTERACTION & ROUTING ---
async def handle_syllabus_selection(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handles button clicks on the Syllabus menu list."""
    query = update.callback_query
    await query.answer()
    
    if query.data == "tier_1":
        lesson_text = (
            "⚙️ *TIER 1 - LESSON 1: JSON Parsing in Server Environments*\n\n"
            "In modern backend services, data arriving from web clients over TCP sockets "
            "almost always arrives formatted as an HTTP payload containing a JSON string.\n\n"
            "Servers cannot calculate metrics or run SQL syntax against a raw text string. "
            "We must convert this serial text structure into an in-memory runtime object "
            "(like a Python Native Dictionary) to process fields cleanly.\n\n"
            "Click below to load the verification code test assertion module."
        )
        keyboard = [[InlineKeyboardButton("📝 Load Verification Quiz", callback_data="start_quiz")]]
        await query.edit_message_text(
            text=lesson_text, parse_mode="Markdown", reply_markup=InlineKeyboardMarkup(keyboard)
        )
        return IN_LESSON
    else:
        await query.edit_message_text(
            text="⚠️ This Tier is locked. Complete Tier 1 first!",
            reply_markup=get_syllabus_keyboard()
        )
        return IDLE

async def trigger_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Transitions the conversation into the active quiz phase."""
    query = update.callback_query
    await query.answer()
    
    quiz_question = (
        "❓ *CODE VERIFICATION TASK:*\n\n"
        "Which core Python standard library module is natively engineered to parse "
        "incoming serialized web strings into accessible dictionaries?"
    )
    await query.edit_message_text(
        text=quiz_question, parse_mode="Markdown", reply_markup=get_quiz_keyboard()
    )
    return IN_QUIZ

async def evaluate_quiz(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Evaluates the user's multiple-choice selection."""
    query = update.callback_query
    await query.answer()
    user_id = query.from_user.id
    
    profile = await get_profile(user_id)
    
    if query.data == "quiz_correct":
        profile.points += 10
        profile.current_lesson = 2
        
        success_message = (
            "🚀 *COMPILATION SUCCESSFUL! (+10 XP)*\n\n"
            "Correct! `json.loads()` converts incoming serialized strings safely "
            "into Python dictionaries.\n\n"
            "You have unlocked Lesson 2! Use /status to check your progress."
        )
        await query.edit_message_text(text=success_message, parse_mode="Markdown")
        return ConversationHandler.END
    else:
        explanations = {
            "quiz_wrong_string": "The `string` module handles operations like text formatting, not deserialization.",
            "quiz_wrong_os": "The `os` module handles operating-system interfaces like environment parameters.",
            "quiz_wrong_req": "The `requests` library is used to send outbound HTTP traffic, not parse text structures.",
        }
        reason = explanations.get(query.data, "Invalid entry mapping.")
        
        retry_message = (
            f"❌ *COMPILATION ERROR: ASSERSTION FAULT*\n\n"
            f"Reason: {reason}\n\n"
            f"Please run diagnostic testing trace logs and try answering again."
        )
        await query.edit_message_text(text=retry_message, parse_mode="Markdown", reply_markup=get_quiz_keyboard())
        return IN_QUIZ

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Gracefully breaks out of the lesson tracking system via /cancel."""
    await update.message.reply_text("Lesson exited. Back to standard listening mode.")
    return ConversationHandler.END

# --- 7. GROUP EVENT HANDLERS ---
async def bot_added_to_group(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Introduces the bot when it is added to a group."""
    result = update.my_chat_member
    if not result:
        return
    old_status = result.old_chat_member.status
    new_status = result.new_chat_member.status
    if old_status in ("left", "kicked") and new_status in ("member", "administrator"):
        chat = result.chat
        if chat.type in (chat.GROUP, chat.SUPERGROUP):
            await chat.send_message(
                "👋 *PyBackendTutor online.*\n\n"
                "I'm your automated backend engineering tutor. "
                "Use `/start` in a private chat to begin your syllabus."
            )

async def welcome_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Welcomes new users who join the group."""
    if not update.message or not update.message.new_chat_members:
        return
    bot_id = (await context.bot.get_me()).id
    for member in update.message.new_chat_members:
        if member.id == bot_id:
            continue
        name = member.mention_html() or member.full_name
        await update.message.reply_html(
            f"🎉 Welcome, {name}! Markoh is Glad to have you here."
        )

async def goodbye_member(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Says goodbye when a member leaves the group."""
    if not update.message or not update.message.left_chat_member:
        return
    member = update.message.left_chat_member
    name = member.mention_html() or member.full_name
    await update.message.reply_html(
        f"👋 Goodbye, {name}! Hope the door hits you on the way out."
    )

# --- 8. RUNTIME ENGINE START ---
def main() -> None:
    # 💡 API key from @BotFather
    TOKEN = os.getenv("TELEGRAM_BOT_TOKEN").strip('"')  # Ensure no extra quotes from .env parsing

    if TOKEN  == "":
        print("❌ ERROR: Please paste your real Telegram Bot Token into line 144 before running!")
        return

    # Build the bot runner instance
    application = Application.builder().token(TOKEN).build()

    # Define how users move between inputs (Syllabus Menu -> Reading Lesson -> Solving Quiz)
    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            IDLE: [CallbackQueryHandler(handle_syllabus_selection, pattern="^tier_")],
            IN_LESSON: [CallbackQueryHandler(trigger_quiz, pattern="^start_quiz$")],
            IN_QUIZ: [CallbackQueryHandler(evaluate_quiz, pattern="^quiz_")],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
        allow_reentry=True
    )

    # Register handlers to the system
    application.add_handler(conv_handler)
    application.add_handler(CommandHandler("status", status_command))
    application.add_handler(ChatMemberHandler(bot_added_to_group, chat_member_types=ChatMemberHandler.MY_CHAT_MEMBER))
    application.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, welcome_new_members))
    application.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, goodbye_member))

    print("⚡ System local runtime online. Press Ctrl+C in this terminal to stop the bot.")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()