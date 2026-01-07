from pyrogram import Client, filters, handlers
import pyrogram
from config import API_ID, API_HASH, SESSION_STRING, KEYWORD_FILTER
from agent import Agent
from task_manager import TaskManager
import logging
import asyncio
import os
import sys
import session_manager

logger = logging.getLogger(__name__)

# Initialize Agent & Task Manager
intelligence_agent = Agent()
tm = TaskManager()
from discussion_buffer import DiscussionBuffer
discussion_buffer = DiscussionBuffer()

# Initialize Client
if SESSION_STRING:
    # Use MemoryStorage to avoid "database is locked" errors permanently
    app = Client("telegram_agent_session", api_id=API_ID, api_hash=API_HASH, session_string=SESSION_STRING, in_memory=True)
else:
    app = Client("telegram_agent_session_local", api_id=API_ID, api_hash=API_HASH)

async def message_handler(client, message):
    # DEBUG: Log everything to understand what's happening
    sender_name = message.chat.title or message.chat.first_name or "Unknown"
    logger.info(f"DEBUG: Received msg from {sender_name} | ID: {message.chat.id} | Type: {message.chat.type} | Outgoing: {message.outgoing}")

    # Skip potential spam or minimal messages
    if not message.text or len(message.text) < 2:
        logger.info("Skipping: Text too short or empty")
        return

    sender = message.chat.title if message.chat.title else message.chat.first_name
    logger.info(f"Processing message from {sender}...")

    # Fetch recent context (last 10 messages) for better analysis
    history = []
    try:
        async for msg in client.get_chat_history(message.chat.id, limit=10):
            sender_name = msg.chat.title or msg.from_user.first_name or "Unknown"
            if msg.from_user:
                sender_name = msg.from_user.first_name
            history.append(f"{sender_name}: {msg.text or '[Media]'}")
        history.reverse() # Oldest first
    except Exception as e:
        logger.warning(f"Failed to fetch history: {e}")
        history = [f"{sender}: {message.text}"]

    context_text = "\n".join(history)

    # Get Memory & Learning Context
    recent_done = await tm.get_recent_done_tasks(limit=5)
    preferences = await tm.get_preference_examples(limit=5)
    
    memory_text = "Recent Finished Tasks:\n" + "\n".join([f"- {t['summary']}" for t in recent_done])
    memory_text += "\n\nUser Preferences (Learning):\n"
    memory_text += "ACCEPTED Tasks:\n" + "\n".join([f"- [P{t['priority']}] {t['summary']} (from {t['sender']}) " + (f"| Note: {', '.join(t['comments'])}" if t['comments'] else "") for t in preferences['accepted']])
    memory_text += "\nREJECTED Tasks:\n" + "\n".join([f"- [P{t['priority']}] {t['summary']} (from {t['sender']}) " + (f"| Note: {', '.join(t['comments'])}" if t['comments'] else "") for t in preferences['rejected']])

    # Analyze with context AND memory
    analysis = await intelligence_agent.analyze_message(context_text, sender, memory_text)
    logger.info(f"Analysis: {analysis}")

    # LOG AUDIT
    try:
        await tm.log_audit(
            message_data={"sender": sender, "text": message.text or "[Media/No Text]"},
            evaluation=analysis
        )
    except Exception as e:
        logger.error(f"Audit log failed: {e}")

    # Add to Task Manager if Priority <= 3 (0=Crit, 1=High, 2=Med, 3=Low) or Action Required
    # Priority 4 is Noise
    if analysis.get('priority', 4) <= 3 or analysis.get('action_required', False):
        try:
            # message.link can sometimes crash if peer is not cached
            safe_link = f"https://t.me/c/{str(message.chat.id)[4:] if str(message.chat.id).startswith('-100') else message.chat.id}/{message.id}"
            try:
                safe_link = message.link
            except Exception:
                pass
                
            task_result = await tm.add_task(
                priority=analysis.get('priority', 0),
                summary=analysis.get('summary', 'No summary'),
                sender=sender,
                link=safe_link,
                deadline=analysis.get('deadline'),
                user_id=message.chat.id
            )
            
            if not task_result.get("is_new", True):
                logger.info(f"Task already exists: {safe_link}. Skipping notification.")
                return

            # Notify user (Silent Mode: Only to Saved Messages)
            notification_text = f"✅ **Task Added from {sender}**\nPriority: {analysis.get('priority', 0)}\nSummary: {analysis.get('summary', 'No summary')}\nLink: {safe_link}"
            
            # If the source was NOT Saved Messages, send a copy to Saved Messages so I know.
            # If it WAS Saved Messages, we can either reply or just let it be. 
            # User asked: "only send to my Saved Messages".
            if message.chat.id != (await client.get_me()).id:
                await client.send_message("me", notification_text)
            else:
                 # Optional: acknowledgment in Saved Messages (the user is "me")
                 await message.reply(f"✅ **Task Added**\nPriority: {analysis.get('priority', 0)}")
        except Exception as e:
            logger.error(f"Failed to add task or reply: {e}")

async def group_digest_listener(client, message):
    """Buffers group messages for daily summary."""
    # Only process Group/Supergroup
    if message.chat.type not in [pyrogram.enums.ChatType.GROUP, pyrogram.enums.ChatType.SUPERGROUP]:
        return
        
    # Skip if it's a command
    if message.text and message.text.startswith("/"):
        return

    # Buffer content
    sender_name = message.from_user.first_name if message.from_user else message.chat.title
    text = message.text or message.caption or "[Media]"
    
    # We buffer everything active. 
    # Optimization: Filter roughly (length > 10?)
    if len(text) > 10:
        discussion_buffer.add_point(message.chat.title or "Unknown Group", sender_name, text)

async def command_handler(client, message):
    """Handles commands like /summary."""
    command = message.text.split()[0].lower()
    
    if command == "/summary":
        logger.info("Generating On-Demand Summary...")
        await message.reply("🔄 Generating Group Discussion Digest...")
        
        buffer_text = discussion_buffer.get_grouped_text()
        if not buffer_text:
             await message.reply("📭 No discussions recorded today.")
             return
             
        summary = await intelligence_agent.summarize_discussions(buffer_text)
        await message.reply(summary)
        
        # Archive it? command usually implies just viewing. 
        # But we can archive "manual" ones too if we want.
        # Let's keep archiving for the daily schedule to avoid duplication.

async def send_daily_briefing(app: Client, tm: TaskManager):
    """Sends a daily summary of top tasks AND discussion digest."""
    logger.info("Generating Daily Briefing...")
    
    # Part 1: Tasks
    data = await tm.get_daily_briefing_tasks()
    task_text = ""
    
    if data['top_tasks']:
        task_text += "**🔥 Top Priorities:**\n"
        for t in data['top_tasks']:
            task_text += f"- (P{t['priority']}) {t['summary']}\n"
    
    if data['deadline_tasks']:
        task_text += "\n**📅 Upcoming Deadlines:**\n"
        for t in data['deadline_tasks']:
             task_text += f"- {t['summary']} ({t.get('deadline')})\n"
             
    # Part 2: Group Digest
    digest_text = ""
    buffer_content = discussion_buffer.get_grouped_text()
    if buffer_content:
        logger.info("Summarizing Group Discussions...")
        digest_text = await intelligence_agent.summarize_discussions(buffer_content)
        # Archive
        discussion_buffer.archive_daily_summary(digest_text)
        discussion_buffer.clear() # Clear buffer after daily report
    
    # Combine
    final_text = "☀️ **Good Morning! Here is your Daily Briefing:**\n\n"
    
    if not task_text and not digest_text:
        final_text += "✅ **All Clear.** No active tasks or discussions."
    else:
        if task_text: final_text += task_text + "\n"
        if digest_text: final_text += "\n" + digest_text + "\n"
        
    final_text += "\n*Check Dashboard: http://localhost:8000*"
    
    # Send to Saved Messages (Me)
    try:
        await app.send_message("me", final_text)
        logger.info("Daily Briefing Sent.")
    except Exception as e:
        logger.error(f"Failed to send briefing: {e}")

async def scheduler(app: Client, tm: TaskManager):
    """Simple loop to check time and send briefing."""
    # Send one immediately on startup for testing/engagement
    await asyncio.sleep(5) # Wait for connection
    await send_daily_briefing(app, tm)
    
    logger.info("Scheduler started.")
    while True:
        # Loop every hour to check if it's 9am
        # For production use apscheduler, but this is fine for MVP
        import datetime
        now = datetime.datetime.now()
        if now.hour == 9 and now.minute == 0:
             await send_daily_briefing(app, tm)
             await asyncio.sleep(61) # Sleep past the minute
        await asyncio.sleep(50)





def is_message_relevant(message, me_id, dynamic_keywords):
    """Refactored logic to check if a message is relevant for the agent."""
    # 1. Saved Messages (Chat "me")
    if message.chat.id == me_id:
        return True
        
    # 2. DMs (Private)
    if message.chat.type == pyrogram.enums.ChatType.PRIVATE:
        # Check if it's NOT from me (incoming DM)
        if not message.from_user.is_self:
            return True # Process all DMs for now (filtered by AI later)
            
    # 3. Mentions
    if message.mentioned:
        return True
        
    # 4. Replies to Me
    if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.is_self:
        return True
    
    # 5. Keywords
    if message.text:
        text = message.text.lower()
        if any(k.lower() in text for k in dynamic_keywords):
            return True
    if message.caption:
        caption = message.caption.lower()
        if any(k.lower() in caption for k in dynamic_keywords):
            return True
            
    return False

def get_message_link(message):
    """Generates a safe link for the message to use as a unique ID."""
    try:
        # Prefer Pyrogram's native link if available
        if message.link:
            return message.link
    except Exception:
        pass
        
    # Fallback construction
    chat_id_str = str(message.chat.id)
    if chat_id_str.startswith('-100'):
        chat_id_str = chat_id_str[4:]
    return f"https://t.me/c/{chat_id_str}/{message.id}"

async def run_catch_up(app: Client, dynamic_keywords):
    """Scans recent dialogs for missed messages during downtime."""
    logger.info("♻️ Running Startup Catch-Up...")
    
    # 0. Pre-fetch existing tasks for Deduplication
    existing_tasks = await tm.get_tasks()
    existing_links = set()
    for t in existing_tasks:
        if t.get('link'):
            existing_links.add(t['link'])
            
    logger.info(f"Loaded {len(existing_links)} existing task links for deduplication.")
    
    me = await app.get_me()
    me_id = me.id
    
    # 1. Fetch recent dialogs
    try:
        dialogs = []
        async for d in app.get_dialogs(limit=20):
            dialogs.append(d.chat.id)
            
        logger.info(f"Scanning {len(dialogs)} active chats for missed tasks...")
        
        count = 0
        skipped = 0
        for chat_id in dialogs:
            # Get last 20 messages
            history = []
            async for msg in app.get_chat_history(chat_id, limit=20):
                history.append(msg)
            
            # Process from oldest to newest
            history.reverse()
            
            for msg in history:
                # Basic relevance check
                if is_message_relevant(msg, me_id, dynamic_keywords):
                    # Deduplication Check
                    msg_link = get_message_link(msg)
                    if msg_link in existing_links:
                        # logger.info(f"Skipping Duplicate: {msg_link}")
                        skipped += 1
                        continue
                        
                    try:
                        await message_handler(app, msg)
                        count += 1
                        # Add to local set to prevent adding same task twice in one run
                        existing_links.add(msg_link) 
                        await asyncio.sleep(0.5) # Rate limit protection
                    except Exception as e:
                        logger.error(f"Error processing catch-up msg: {e}")
                        
        logger.info(f"♻️ Catch-Up Complete. Processed {count} new messages. Skipped {skipped} duplicates.")
        
    except Exception as e:
        logger.error(f"Catch-Up Failed: {e}")

async def start_listener():
    logger.info("Client initialized. Starting...")
    
    # CRITICAL FIX: Rebind app execution loop to the current running loop
    import asyncio
    running_loop = asyncio.get_running_loop()
    app.loop = running_loop
    app.dispatcher.loop = running_loop
    # Re-create queue on the new loop to ensure compatibility
    app.dispatcher.updates_queue = asyncio.Queue()

    # Register Handlers
    logger.info("Registering handlers...")

    # Dynamic Keywords
    dynamic_keywords = list(KEYWORD_FILTER) # Start with config keywords
    
    # Custom Filter: Start Listener
    # 1. Replies to ME
    # 2. Keywords (Dynamic)
    async def relevant_filter(_, __, message):
        # We need 'me' ID for the helper, but inside filter it's hard to get async 'me' every time.
        # We'll use a cached ID or just checking 'is_self' on message objects.
        # For efficiency, we replicate the logic slightly or use the helper if we had 'me_id'.
        # Since 'is_message_relevant' needs me_id for Saved Messages check, we can rely on filters.chat("me") for that.
        
        if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.is_self:
            return True
        
        if message.text:
            text = message.text.lower()
            if any(k.lower() in text for k in dynamic_keywords):
                return True
        if message.caption:
            caption = message.caption.lower()
            if any(k.lower() in caption for k in dynamic_keywords):
                return True
                
        return False

    custom_relevance_filter = filters.create(relevant_filter)

    # Register Group Digest Listener (Catch-all for groups)
    app.add_handler(handlers.MessageHandler(group_digest_listener, filters.group), group=1)
    
    # Register Command Handler (Privacy: Only me)
    app.add_handler(handlers.MessageHandler(command_handler, filters.command("summary") & filters.me), group=2)
    
    # Existing Handler (Priority Logic)
    app.add_handler(handlers.MessageHandler(message_handler, 
        filters.private | filters.mentioned | filters.chat("me") | custom_relevance_filter
    ), group=0)

    # Start the client
    # 0. Validate Session (Auto-Renewal)
    new_session, updated = await session_manager.ensure_session(API_ID, API_HASH, SESSION_STRING)
    
    if updated:
        logger.info("Session updated. Saving and restarting...")
        session_manager.update_env_session(new_session)
        
        # CRITICAL FIX: Update os.environ so the new process inherits the new session
        # otherwise load_dotenv will see the old empty env var and not override it.
        os.environ["SESSION_STRING"] = new_session
        
        logger.info("Restarting process to apply new session...")
        # Restart the current script
        os.execv(sys.executable, [sys.executable] + sys.argv)
        return

    # If valid, start
    await app.start()
    
    # Init Keywords
    me = await app.get_me()
    if me.first_name: dynamic_keywords.append(me.first_name)
    if me.last_name: dynamic_keywords.append(me.last_name)
    if me.username: dynamic_keywords.append(me.username)
    logger.info(f"Initialized Keyword Filter: {dynamic_keywords}")
    
    # START CATCH-UP
    # Disabled to prevent duplicates: Pyrogram automatically fetches missed updates on persistent sessions.
    # await run_catch_up(app, dynamic_keywords)
    logger.info("Startup Catch-Up DISABLED (Relying on Native Updates)")
    
    # Start Scheduler
    asyncio.create_task(scheduler(app, tm))

    try:
        await app.send_message("me", "⚡ **Agent Just Started** ⚡\n_Group Digest Active._")
        logger.info("Startup message sent to 'me'")
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")
    logger.info("Client started successfully.")
