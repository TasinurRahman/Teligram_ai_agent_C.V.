import logging
import asyncio
import os
import sys
import time
import io
import threading
import requests
from http.server import HTTPServer, BaseHTTPRequestHandler
from telegram import Update, ReactionTypeEmoji
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, ContextTypes, filters
from telegram.error import Conflict
import config
from agent_core import AutonomousAgentCore
from self_upgrade_engine import SelfUpgradeEngine
from tools.image_generator import ImageGeneratorTool

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

agent = AutonomousAgentCore()
upgrade_engine = SelfUpgradeEngine(agent.memory, agent.router)
voice_confirmations = {}

async def send_response_safely(update: Update, response: str, context: ContextTypes.DEFAULT_TYPE = None):
    """Sends response in chunks if it exceeds Telegram's 4096 character limit."""
    if not response:
        response = "কোনো উত্তর তৈরি করা সম্ভব হয়নি।"
    
    if response.startswith("FILE:"):
        file_path = response.replace("FILE:", "").strip()
        if os.path.exists(file_path):
            await update.message.reply_document(document=open(file_path, "rb"), reply_to_message_id=update.message.message_id)
            return
        else:
            response = "ফাইলটি তৈরি করা সম্ভব হয়নি।"

    if response.startswith("GENERATE_IMAGE::"):
        prompt = response.replace("GENERATE_IMAGE::", "").strip()
        status_msg = await update.message.reply_text("🎨 AI ছবি তৈরি হচ্ছে... একটু অপেক্ষা করুন।", reply_to_message_id=update.message.message_id)
        loop = asyncio.get_event_loop()
        img_bytes = await loop.run_in_executor(None, ImageGeneratorTool.generate_image_for_telegram, prompt)
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
        except Exception:
            pass
        if img_bytes:
            await update.message.reply_photo(
                photo=io.BytesIO(img_bytes),
                caption=f"✨ Generated: *{prompt[:200]}*",
                reply_to_message_id=update.message.message_id,
                parse_mode="Markdown"
            )
        else:
            await update.message.reply_text("❌ ছবি তৈরি করতে সমস্যা হয়েছে। আবার চেষ্টা করুন।", reply_to_message_id=update.message.message_id)
        return
    
    if len(response) > 4000:
        chunks = [response[i:i+4000] for i in range(0, len(response), 4000)]
        for chunk in chunks:
            await update.message.reply_text(chunk, reply_to_message_id=update.message.message_id)
    else:
        await update.message.reply_text(response, reply_to_message_id=update.message.message_id)

async def try_react_to_message(update: Update, context: ContextTypes.DEFAULT_TYPE, text: str):
    """Dynamically reacts with Telegram emojis based on sentiment, humor, or technical tone."""
    if not update.message or not text:
        return
    try:
        text_lower = text.lower()
        if any(w in text_lower for w in ["haha", "lol", "rofl", "moza", "hasir", "hasi", "joke", "😂", "🤣", "xd", "funny"]):
            await context.bot.set_message_reaction(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
                reaction=[ReactionTypeEmoji("😂")]
            )
        elif any(w in text_lower for w in ["boss", "great", "shabash", "best", "sera", "awesome", "valovabe", "valo lagse", "🔥"]):
            await context.bot.set_message_reaction(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
                reaction=[ReactionTypeEmoji("🔥")]
            )
        elif any(w in text_lower for w in ["code", "hack", "bug", "security", "exploit", "pentest", "ctf", "python", "script", "terminal"]):
            await context.bot.set_message_reaction(
                chat_id=update.effective_chat.id,
                message_id=update.message.message_id,
                reaction=[ReactionTypeEmoji("⚡")]
            )
    except Exception:
        pass

# ============ TELEGRAM COMMANDS ============

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_info = agent.memory.get_or_create_user(str(user.id), user.username or "")
    is_admin = agent.memory.is_admin(str(user.id), user.username or "")
    
    limit_text = "আনলিমিটেড" if is_admin else f"{user_info['daily_limit']} রিকোয়েস্ট"
    
    welcome = (
        f"🏛️ **CyberVerse Autonomous AI System**\n"
        f"স্বাগতম, {user.first_name}!\n\n"
        f"👑 **আপনার ভূমিকা:** `{'SUPER ADMIN (CREATOR)' if is_admin else user_info['role'].upper()}`\n"
        f"📊 **দৈনিক কোটা:** `{limit_text}`\n\n"
        f"💼 **সিস্টেমের ক্ষমতা ও ফিচার:**\n"
        f"• 🎙️ **ভয়েস নোট:** স্পষ্ট ট্রান্সক্রিপশন সহ যেকোনো ভাষায় তাৎক্ষণিক উত্তর\n"
        f"• 📸 **ছবি/স্ক্রিনশট:** নিখুঁত OCR, কোড ও ইন্টারফেস বিশ্লেষণ\n"
        f"• 🎥 **ভিডিও অ্যানালাইসিস:** ভিডিও ফ্রেম পর্যবেক্ষণ করে গভীর সমাধান\n"
        f"• 📄 **ডকুমেন্ট রিডার:** PDF, Word (.docx), PowerPoint (.pptx) সামারি\n"
        f"• 🎨 **Figma & Web UI:** পেজ-বাই-পেজ আধুনিক রেসপনসিভ ডিজাইন\n"
        f"• ⚡ **কোড এক্সিকিউশন:** কোড সরাসরি ব্যাকএন্ডে রান করে আউটপুট প্রদর্শন (`/run`)\n"
    )

    if is_admin:
        welcome += (
            f"\n⚡ **এডমিন সুপারপাওয়ার কমান্ডস (শুধুমাত্র আপনার জন্য):**\n"
            f"• `/admin` - সম্পূর্ণ এডমিন কন্ট্রোল ড্যাশবোর্ড ও স্ট্যাটাস\n"
            f"• `/users` - সকল ব্যবহারকারী ও তাদের ব্যবহার তালিকা\n"
            f"• `/setlimit <ID> <limit>` - যেকোনো ইউজারের লিমিট বাড়ানো বা কমানো\n"
            f"• `/ban <ID>` - ক্ষতিকর বা অতিরিক্ত রিকোয়েস্টকারীকে ব্লক করা\n"
            f"• `/unban <ID>` - ব্লক খুলে দেওয়া\n"
            f"• `/upgrade` - তাৎক্ষণিক দৈনিক সেলফ-আপগ্রেড চালানো ও রিপোর্ট দেখা\n"
        )

    await update.message.reply_text(welcome, parse_mode="Markdown")

async def run_code_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_code = " ".join(context.args)
    if not user_code:
        await update.message.reply_text("ব্যবহার নিয়ম: `/run print('Hello World')`", parse_mode="Markdown")
        return

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
    loop = asyncio.get_event_loop()
    output = await loop.run_in_executor(None, agent.code_runner.run_python, user_code)
    await update.message.reply_text(f"⚡ **আউটপুট:**\n```\n{output}\n```", reply_to_message_id=update.message.message_id, parse_mode="Markdown")

# ============ ADMIN SUPERPOWERS ============

async def admin_dashboard(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not agent.memory.is_admin(str(user.id), user.username or ""):
        await update.message.reply_text("⛔ এই কমান্ডটি শুধুমাত্র সুপ্রিম ক্রিয়েটর (Tasin) এর জন্য সংরক্ষিত।")
        return

    stats = agent.memory.get_system_stats()
    latest_up = agent.memory.get_latest_self_upgrade()
    latest_date = latest_up['date'] if latest_up else "আজকে এখনও চালানো হয়নি"

    text = (
        f"👑 **CyberVerse Creator Control Center**\n"
        f"হ্যালো বস Tasin! আপনার সিস্টেম স্ট্যাটাস:\n\n"
        f"👥 মোট রেজিস্টার্ড ইউজার: `{stats['total_users']}` জন\n"
        f"📈 আজকের মোট সফল রিকোয়েস্ট: `{stats['total_requests_today']}` টি\n"
        f"🚫 ব্যান করা ইউজার: `{stats['banned_users']}` জন\n"
        f"🧠 সর্বশেষ সেলফ-আপগ্রেড: `{latest_date}`\n\n"
        f"⚙️ **ম্যানেজমেন্ট কমান্ডস:**\n"
        f"`/users` — সব ইউজারের বিস্তারিত তালিকা\n"
        f"`/setlimit <id> <limit>` — লিমিট সেট (যেমন: `/setlimit 123456 100`)\n"
        f"`/ban <id>` — ইউজার ব্যান\n"
        f"`/unban <id>` — ব্যান আনলক\n"
        f"`/upgrade` — এখনই সিস্টেমের সেলফ-আপগ্রেড রান করুন"
    )
    await update.message.reply_text(text, parse_mode="Markdown")

async def admin_list_users(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not agent.memory.is_admin(str(user.id), user.username or ""):
        await update.message.reply_text("⛔ শুধুমাত্র প্রশাসকের অনুমতি রয়েছে।")
        return

    all_users = agent.memory.list_all_users()
    if not all_users:
        await update.message.reply_text("এখনও কোনো ইউজার রেজিস্টার্ড হয়নি।")
        return

    lines = ["👥 **সকল ব্যবহারকারীর তালিকা:**\n"]
    for u in all_users:
        uid, uname, role, limit, used, allowed = u
        status_icon = "✅" if allowed else "🚫 BANNED"
        u_handle = f"@{uname}" if uname else "No Username"
        lines.append(f"• `{uid}` ({u_handle}) | {role.upper()} | ব্যবহার: `{used}/{limit}` | {status_icon}")

    await send_response_safely(update, "\n".join(lines))

async def admin_set_limit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not agent.memory.is_admin(str(user.id), user.username or ""):
        await update.message.reply_text("⛔ শুধুমাত্র সুপ্রিম ক্রিয়েটর (Tasin) এর অনুমতি রয়েছে।")
        return
    try:
        target_id = context.args[0]
        new_limit = int(context.args[1])
        agent.memory.update_user_limit(target_id, new_limit)
        await update.message.reply_text(f"✅ ব্যবহারকারী `{target_id}` এর দৈনিক লিমিট `{new_limit}` এ আপডেট করা হয়েছে।")
    except Exception:
        await update.message.reply_text("ব্যবহার নিয়ম: `/setlimit <telegram_id> <limit>`", parse_mode="Markdown")

async def admin_ban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not agent.memory.is_admin(str(user.id), user.username or ""):
        await update.message.reply_text("⛔ শুধুমাত্র সুপ্রিম ক্রিয়েটর (Tasin) এর অনুমতি রয়েছে।")
        return
    try:
        target_id = context.args[0]
        if target_id == str(user.id):
            await update.message.reply_text("আপনি নিজেকে ব্যান করতে পারবেন না!")
            return
        agent.memory.ban_user(target_id)
        await update.message.reply_text(f"🚫 ব্যবহারকারী `{target_id}` কে সফলভাবে ব্যান করা হয়েছে।")
    except Exception:
        await update.message.reply_text("ব্যবহার নিয়ম: `/ban <telegram_id>`", parse_mode="Markdown")

async def admin_unban_user(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    if not agent.memory.is_admin(str(user.id), user.username or ""):
        await update.message.reply_text("⛔ শুধুমাত্র সুপ্রিম ক্রিয়েটর (Tasin) এর অনুমতি রয়েছে।")
        return
    try:
        target_id = context.args[0]
        agent.memory.unban_user(target_id)
        await update.message.reply_text(f"✅ ব্যবহারকারী `{target_id}` এর ব্যান প্রত্যাহার করা হয়েছে।")
    except Exception:
        await update.message.reply_text("ব্যবহার নিয়ম: `/unban <telegram_id>`", parse_mode="Markdown")

async def admin_trigger_upgrade(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Runs autonomous self-upgrade cycle and reports results immediately."""
    user = update.effective_user
    if not agent.memory.is_admin(str(user.id), user.username or ""):
        await update.message.reply_text("⛔ শুধুমাত্র সুপ্রিম ক্রিয়েটর (Tasin) এর অনুমতি রয়েছে।")
        return

    status_msg = await update.message.reply_text("🧠 অটোনমাস সেলফ-আপগ্রেড সাইকেল শুরু হচ্ছে... জ্ঞান ও মেমোরি রিফাইন করা হচ্ছে...")
    
    loop = asyncio.get_event_loop()
    report = await loop.run_in_executor(None, upgrade_engine.perform_daily_upgrade)

    try:
        await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
    except Exception:
        pass

    full_text = f"🌅 **দৈনিক অটোনমাস সেলফ-আপগ্রেড সম্পন্ন**\n\n{report}"
    await send_response_safely(update, full_text)

# ============ MESSAGE HANDLERS ============

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_text = update.message.text
    user_id_str = str(user.id)

    if user_id_str in voice_confirmations:
        if any(word in user_text.lower() for word in ["হ্যাঁ", "ha", "yes", "ji", "hea", "humm", "hmm"]):
            transcription = voice_confirmations.pop(user_id_str)
            await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, agent.process_message, user_id_str, user.username or "", transcription
            )
            await send_response_safely(update, response, context)
            return
        elif any(word in user_text.lower() for word in ["না", "na", "no"]):
            voice_confirmations.pop(user_id_str)
            await send_response_safely(update, "ঠিক আছে, বাতিল করা হলো। আপনি আবার বলতে পারেন।")
            return

    # Dynamic reaction (laughing, hype, or tech)
    await try_react_to_message(update, context, user_text)

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    loop = asyncio.get_event_loop()

    # If user is requesting a document creation, show a status message
    is_doc_request = any(t in user_text.lower() for t in ["make doc", "create doc", "word document", "doc file", "ardock file", "ডক ফাইল", "ডকুমেন্ট"])
    if is_doc_request:
        status_msg = await update.message.reply_text("📄 ডকুমেন্ট তৈরি হচ্ছে... একটু অপেক্ষা করুন।", reply_to_message_id=update.message.message_id)
        response = await loop.run_in_executor(
            None, agent.process_message, user_id_str, user.username or "", user_text
        )
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
        except Exception:
            pass
    else:
        response = await loop.run_in_executor(
            None, agent.process_message, user_id_str, user.username or "", user_text
        )
    await send_response_safely(update, response, context)

async def handle_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    caption = update.message.caption or ""

    await try_react_to_message(update, context, caption)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        photo = update.message.photo[-1]
        file = await context.bot.get_file(photo.file_id)
        
        file_bytes = io.BytesIO()
        await file.download_to_memory(file_bytes)
        img_data = file_bytes.getvalue()

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, agent.process_image, str(user.id), user.username or "", img_data, caption
        )
        await send_response_safely(update, response, context)
    except Exception as e:
        logger.error(f"Error handling photo: {e}")
        await update.message.reply_text(f"ছবি বিশ্লেষণ করতে সমস্যা হয়েছে: {str(e)}", reply_to_message_id=update.message.message_id)

async def handle_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    caption = update.message.caption or ""

    await try_react_to_message(update, context, caption)
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        video = update.message.video or update.message.animation
        if video.file_size and video.file_size > 20 * 1024 * 1024:
            await update.message.reply_text("ভিডিও সাইজ ২০ মেগাবাইটের বেশি। অনুগ্রহ করে ছোট ক্লিপ পাঠান।", reply_to_message_id=update.message.message_id)
            return

        file = await context.bot.get_file(video.file_id)
        file_bytes = io.BytesIO()
        await file.download_to_memory(file_bytes)
        video_data = file_bytes.getvalue()

        status_msg = await update.message.reply_text("🎥 ভিডিও ফ্রেম এক্সট্র্যাক্ট ও বিশ্লেষণ করা হচ্ছে...", reply_to_message_id=update.message.message_id)

        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, agent.process_video, str(user.id), user.username or "", video_data, caption
        )
        
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
        except Exception:
            pass
            
        await send_response_safely(update, response, context)
    except Exception as e:
        logger.error(f"Error handling video: {e}")
        await update.message.reply_text(f"ভিডিও প্রসেসিং ত্রুটি: {str(e)}", reply_to_message_id=update.message.message_id)

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        voice = update.message.voice or update.message.audio
        file = await context.bot.get_file(voice.file_id)
        
        file_bytes = io.BytesIO()
        await file.download_to_memory(file_bytes)
        audio_data = file_bytes.getvalue()

        filename = "voice.ogg" if update.message.voice else (file.file_path.split("/")[-1] if file.file_path else "audio.mp3")

        loop = asyncio.get_event_loop()
        transcription = await loop.run_in_executor(
            None, agent.router.transcribe_audio, audio_data, filename
        )

        if not transcription:
            await update.message.reply_text("দুঃখিত, ভয়েসটি স্পষ্টভাবে বোঝা যায়নি। অনুগ্রহ করে আরেকবার পরিষ্কারভাবে বলুন।", reply_to_message_id=update.message.message_id)
            return

        await try_react_to_message(update, context, transcription)

        confirm_header = f"🎙️ **শনাক্তকৃত বার্তা:**\n> *\"{transcription}\"*\n\n"
        voice_confirmations[str(user.id)] = transcription
        
        full_reply = f"{confirm_header}🤖 **আপনি কি এই মেসেজটি পাঠাতে চান? (হ্যাঁ/না)**"
        await send_response_safely(update, full_reply, context)

    except Exception as e:
        logger.error(f"Error handling voice: {e}")
        await update.message.reply_text(f"ভয়েস প্রক্রিয়া করতে সমস্যা হয়েছে: {str(e)}", reply_to_message_id=update.message.message_id)

async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    doc = update.message.document
    caption = update.message.caption or ""
    filename = (doc.file_name or "document").lower()

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        if doc.file_size and doc.file_size > 20 * 1024 * 1024:
            await update.message.reply_text("ফাইলটি অনেক বড় (২০ মেগাবাইটের বেশি)।", reply_to_message_id=update.message.message_id)
            return

        file = await context.bot.get_file(doc.file_id)
        file_bytes = io.BytesIO()
        await file.download_to_memory(file_bytes)
        data = file_bytes.getvalue()

        # --- iPhone HEIC image ---
        if filename.endswith((".heic", ".heif")):
            status_msg = await update.message.reply_text("📸 iPhone ছবি রূপান্তর ও বিশ্লেষণ হচ্ছে...", reply_to_message_id=update.message.message_id)
            try:
                from PIL import Image
                import pillow_heif
                pillow_heif.register_heif_opener()
                img = Image.open(io.BytesIO(data))
                buf = io.BytesIO()
                img.convert("RGB").save(buf, format="JPEG", quality=90)
                jpeg_data = buf.getvalue()
            except Exception:
                jpeg_data = data  # fallback: pass raw
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, agent.process_image, str(user.id), user.username or "", jpeg_data, caption
            )
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
            except Exception:
                pass
            await send_response_safely(update, response, context)
            return

        # --- iPhone MOV / any video file ---
        if filename.endswith((".mov", ".mp4", ".avi", ".mkv", ".webm", ".3gp")):
            if doc.file_size and doc.file_size > 20 * 1024 * 1024:
                await update.message.reply_text("ভিডিও সাইজ ২০ মেগাবাইটের বেশি।", reply_to_message_id=update.message.message_id)
                return
            status_msg = await update.message.reply_text("🎥 ভিডিও ফ্রেম রিড ও বিশ্লেষণ হচ্ছে...", reply_to_message_id=update.message.message_id)
            loop = asyncio.get_event_loop()
            response = await loop.run_in_executor(
                None, agent.process_video, str(user.id), user.username or "", data, caption
            )
            try:
                await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
            except Exception:
                pass
            await send_response_safely(update, response, context)
            return

        # --- Regular document ---
        status_msg = await update.message.reply_text(f"📄 `{doc.file_name}` পড়া ও বিশ্লেষণ হচ্ছে...", reply_to_message_id=update.message.message_id)
        loop = asyncio.get_event_loop()
        response = await loop.run_in_executor(
            None, agent.process_document, str(user.id), user.username or "", data, doc.file_name or "document", caption
        )
        try:
            await context.bot.delete_message(chat_id=update.effective_chat.id, message_id=status_msg.message_id)
        except Exception:
            pass
        await send_response_safely(update, response, context)
    except Exception as e:
        logger.error(f"Error handling document: {e}")
        await update.message.reply_text(f"ফাইল পড়তে সমস্যা হয়েছে: {str(e)}", reply_to_message_id=update.message.message_id)

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    if isinstance(context.error, Conflict):
        logger.info("Temporary polling conflict. Auto-recovering...")
    else:
        logger.error("Bot error:", exc_info=context.error)

# ============ DAILY SELF-UPGRADE BACKGROUND ROUTINE ============

def start_daily_upgrade_background(application):
    """Spawns background thread that runs daily upgrade every 24h and sends report to Admin."""
    def run_cycle():
        time.sleep(120)  # Wait 2 mins after boot
        while True:
            try:
                report = upgrade_engine.perform_daily_upgrade()
                admin_id = str(config.ADMIN_TELEGRAM_ID)
                if admin_id and application.bot:
                    asyncio.run(application.bot.send_message(
                        chat_id=admin_id,
                        text=f"🌅 **দৈনিক অটোনমাস সেলফ-আপগ্রেড সম্পন্ন**\n\n{report}",
                        parse_mode="Markdown"
                    ))
            except Exception as e:
                logger.error(f"Error in daily upgrade background job: {e}")
            time.sleep(86400) # Every 24 hours

    threading.Thread(target=run_cycle, daemon=True).start()

# ============ HEALTH CHECK & KEEP-ALIVE ============

class HealthCheckHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/plain")
        self.end_headers()
        self.wfile.write(b"CyberVerse Autonomous Principal Online!")
    def do_HEAD(self):
        self.do_GET()
    def log_message(self, format, *args):
        pass

def start_health_server():
    port = int(os.environ.get("PORT", 8080))
    server = HTTPServer(("0.0.0.0", port), HealthCheckHandler)
    logger.info(f"Health check running on port {port}")
    server.serve_forever()

def keep_alive_loop():
    time.sleep(15)
    url = os.environ.get("RENDER_EXTERNAL_URL", "https://cyberverse-ai.onrender.com")
    while True:
        try:
            requests.get(url, timeout=10)
        except Exception:
            pass
        time.sleep(240)

# ============ MAIN ============

def main():
    if not config.TELEGRAM_BOT_TOKEN:
        print("TELEGRAM_BOT_TOKEN missing!")
        return

    threading.Thread(target=start_health_server, daemon=True).start()
    threading.Thread(target=keep_alive_loop, daemon=True).start()

    app = ApplicationBuilder().token(config.TELEGRAM_BOT_TOKEN).build()

    # User Commands
    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("run", run_code_command))

    # Exclusive Admin Commands
    app.add_handler(CommandHandler("admin", admin_dashboard))
    app.add_handler(CommandHandler("users", admin_list_users))
    app.add_handler(CommandHandler("setlimit", admin_set_limit))
    app.add_handler(CommandHandler("ban", admin_ban_user))
    app.add_handler(CommandHandler("unban", admin_unban_user))
    app.add_handler(CommandHandler("upgrade", admin_trigger_upgrade))
    app.add_handler(CommandHandler("report", admin_trigger_upgrade))

    # Media and Message Handlers
    app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))
    app.add_handler(MessageHandler(filters.PHOTO, handle_photo))
    app.add_handler(MessageHandler(filters.VIDEO | filters.ANIMATION, handle_video))
    app.add_handler(MessageHandler(filters.VOICE | filters.AUDIO, handle_voice))
    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_error_handler(error_handler)

    # Start scheduled 24h self-upgrade notification thread
    start_daily_upgrade_background(app)

    print("[SUCCESS] CyberVerse Autonomous Multimodal AI is active.")
    app.run_polling()

if __name__ == "__main__":
    main()
