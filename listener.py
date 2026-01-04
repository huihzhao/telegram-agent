from pyrogram import Client, filters, handlers
from config import API_ID, API_HASH, SESSION_STRING
from agent import Agent
from task_manager import TaskManager
import logging
import asyncio

logger = logging.getLogger(__name__)

# Initialize Agent & Task Manager
intelligence_agent = Agent()
tm = TaskManager()

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
    recent_done = tm.get_recent_done_tasks(limit=5)
    preferences = tm.get_preference_examples(limit=5)
    
    memory_text = "Recent Finished Tasks:\n" + "\n".join([f"- {t['summary']}" for t in recent_done])
    memory_text += "\n\nUser Preferences (Learning):\n"
    memory_text += "ACCEPTED Tasks:\n" + "\n".join([f"- {t['summary']} (from {t['sender']})" for t in preferences['accepted']])
    memory_text += "\nREJECTED Tasks:\n" + "\n".join([f"- {t['summary']} (from {t['sender']})" for t in preferences['rejected']])

    # Analyze with context AND memory
    analysis = await intelligence_agent.analyze_message(context_text, sender, memory_text)
    logger.info(f"Analysis: {analysis}")

    # Add to Task Manager if important (Threshold > 4) or Action Required
    # Restored to 4 to filter noise (e.g. "hi")
    if analysis.get('priority', 0) >= 4 or analysis.get('action_required', False):
        try:
            # message.link can sometimes crash if peer is not cached
            safe_link = f"https://t.me/c/{str(message.chat.id)[4:] if str(message.chat.id).startswith('-100') else message.chat.id}/{message.id}"
            try:
                safe_link = message.link
            except Exception:
                pass
                
            tm.add_task(
                priority=analysis.get('priority', 0),
                summary=analysis.get('summary', 'No summary'),
                sender=sender,
                link=safe_link,
                deadline=analysis.get('deadline'),
                user_id=message.chat.id
            )
            # Notify user in Telegram
            await message.reply(f"✅ **Task Added**\nPriority: {analysis.get('priority', 0)}\nSummary: {analysis.get('summary', 'No summary')}")
        except Exception as e:
            logger.error(f"Failed to add task or reply: {e}")

async def send_daily_briefing(app: Client, tm: TaskManager):
    """Sends a daily summary of top tasks."""
    logger.info("Generating Daily Briefing...")
    data = tm.get_daily_briefing_tasks()
    
    if not data['top_tasks'] and not data['deadline_tasks']:
        # Send a "All Clear" message instead of silence, so user knows it ran
        text = "☀️ **Good Morning!**\n\n✅ **You have Zero Active Tasks.**\nEnjoy your day! details at http://localhost:8000"
        try:
            await app.send_message("me", text)
            logger.info("Daily Briefing Sent (Empty).")
        except Exception as e:
            logger.error(f"Failed to send briefing: {e}")
        return

    text = "☀️ **Good Morning! Here is your Daily Briefing:**\n\n"
    
    if data['top_tasks']:
        text += "**🔥 Top Priorities:**\n"
        for t in data['top_tasks']:
            text += f"- (P{t['priority']}) {t['summary']}\n"
    
    if data['deadline_tasks']:
        text += "\n**📅 Upcoming Deadlines:**\n"
        for t in data['deadline_tasks']:
             text += f"- {t['summary']} ({t.get('deadline')})\n"
             
    text += "\n*Check Dashboard: http://localhost:8000*"
    
    # Send to Saved Messages (Me)
    try:
        await app.send_message("me", text)
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
    

    # Custom Filter: Start Listener
    # 1. Replies to ME
    # 2. Keywords ("Jackie")
    # Dynamic Keywords
    dynamic_keywords = []

    # Custom Filter: Start Listener
    # 1. Replies to ME
    # 2. Keywords (Dynamic)
    async def relevant_filter(_, __, message):
        # 1. Reply to Me
        if message.reply_to_message and message.reply_to_message.from_user and message.reply_to_message.from_user.is_self:
            return True
        
        # 2. Keywords
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

    # Message Handlers
    # Filter: DMs OR Mentions OR Saved Messages OR Replies to Me OR Keywords
    app.add_handler(handlers.MessageHandler(message_handler, 
        filters.private | filters.mentioned | filters.chat("me") | custom_relevance_filter
    ), group=0)

    # Start the client
    await app.start()
    
    # Start Scheduler
    asyncio.create_task(scheduler(app, tm))
    
    # Init Keywords
    me = await app.get_me()
    if me.first_name: dynamic_keywords.append(me.first_name)
    if me.last_name: dynamic_keywords.append(me.last_name)
    if me.username: dynamic_keywords.append(me.username)
    logger.info(f"Initialized Keyword Filter: {dynamic_keywords}")

    try:
        await app.send_message("me", "⚡ **Agent Just Started** ⚡\nSend me a message to test!")
        logger.info("Startup message sent to 'me'")
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")
    logger.info("Client started successfully.")
