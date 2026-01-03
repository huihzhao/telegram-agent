from pyrogram import Client, filters, handlers
from config import API_ID, API_HASH, SESSION_STRING
from agent import Agent
from task_manager import TaskManager
import logging

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

    # Analyze
    analysis = await intelligence_agent.analyze_message(message.text, sender)
    logger.info(f"Analysis: {analysis}")

    # Add to Task Manager if important (Threshold > 7) or Action Required
    # DEBUG: Lowered to 0 to ensure dashboard appears
    if analysis.get('priority', 0) >= 0 or analysis.get('action_required', False):
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
                deadline=analysis.get('deadline')
            )
            # Notify user in Telegram
            await message.reply(f"✅ **Task Added**\nPriority: {analysis.get('priority', 0)}\nSummary: {analysis.get('summary', 'No summary')}")
        except Exception as e:
            logger.error(f"Failed to add task or reply: {e}")





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
    
    # Message Handlers
    app.add_handler(handlers.MessageHandler(message_handler, 
        filters.private | filters.user("me") | filters.outgoing | filters.incoming
    ), group=0)

    # Start the client
    await app.start()

    try:
        await app.send_message("me", "⚡ **Agent Just Started** ⚡\nSend me a message to test!")
        logger.info("Startup message sent to 'me'")
    except Exception as e:
        logger.error(f"Failed to send startup message: {e}")
    logger.info("Client started successfully.")
