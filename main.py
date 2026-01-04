import asyncio
import logging
import uvicorn
# Load Config & Env FIRST
from config import API_ID, API_HASH
from listener import start_listener, tm, app as client_app
import server
import pyrogram

# Configure Logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logging.getLogger("uvicorn.access").setLevel(logging.INFO)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)

async def on_task_done(summary: str):
    """Callback when a task is marked done via the Web UI."""
    try:
        if client_app.is_connected:
            await client_app.send_message("me", f"✅ **Task Completed**\n_{summary}_")
    except Exception as e:
        logger.error(f"Failed to send completion notification: {e}")

async def run_server():
    """Runs the FastAPI server."""
    # Install handlers=False to let asyncio handling signals
    config = uvicorn.Config(server.app, host="0.0.0.0", port=8000, log_level="warning")
    server_instance = uvicorn.Server(config)
    # Hack to allow uvicorn to be cancelled quickly
    server_instance.install_signal_handlers = lambda: None
    await server_instance.serve()

async def main():
    if not API_ID or not API_HASH:
        logger.error("API_ID and API_HASH must be set in .env")
        return

    # Dependency Injection
    server.task_manager = tm
    server.notification_callback = on_task_done

    logger.info("Starting Telegram Intelligence Agent...")
    
    # 1. Start Telegram Client FIRST
    await start_listener()
    
    logger.info("Telegram Client Connected.")
    logger.info("Starting Web Dashboard at http://localhost:8000...")

    # 2. Run Server as background task
    server_task = asyncio.create_task(run_server())

    # 3. Idle until signal
    try:
        await pyrogram.idle()
    except asyncio.CancelledError:
        logger.info("Idle cancelled.")
    finally:
        logger.info("Shutting down services...")
        
        # Stop Server
        server_task.cancel()
        try:
            await server_task
        except asyncio.CancelledError:
            pass
            
        logger.info("Stopping Telegram Client...")
        if client_app.is_connected:
            try:
                # Force timeout on stop to prevent hanging
                await asyncio.wait_for(client_app.stop(), timeout=5.0)
            except asyncio.TimeoutError:
                logger.warning("Telegram Client stop timed out. Forcing exit.")
        logger.info("Telegram Client Stopped.")

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
    except Exception as e:
        logger.error(f"Fatal error: {e}")
