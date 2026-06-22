import logging, os, sys, asyncio
from pathlib import Path
from dotenv import load_dotenv
from telegram import BotCommand

load_dotenv()
Path("data").mkdir(exist_ok=True)
logging.basicConfig(level="INFO",
format="%(asctime)s %(name)s: %(message)s",
handlers=[logging.StreamHandler(sys.stdout)])
logger = logging.getLogger("titan")

async def run():
    logger.info("TITAN V1 STARTING")
    token = os.getenv("BOT_TOKEN")
    if not token:
        logger.critical("BOT_TOKEN not set")
        sys.exit(1)
    from db.migrations import run_migrations
    await run_migrations()
    logger.info("Database ready")
    from telegram.ext import ApplicationBuilder
    from bot.handlers.start import register_start
    from bot.handlers.admin import register_admin
    from bot.handlers.signals import register_signals
    from bot.handlers.journal import register_journal
    app = ApplicationBuilder().token(token).build()
    register_start(app)
    register_admin(app)
    register_signals(app)
    register_journal(app)
    
    # Set bot commands in Telegram menu
    commands = [
        BotCommand("start", "Welcome to Titan V1"),
        BotCommand("help", "View all commands"),
        BotCommand("status", "Check your account status"),
        BotCommand("signal", "Generate trade signal (pair arg)"),
        BotCommand("regime", "Check market regime (pair arg)"),
        BotCommand("score", "View confidence breakdown (pair arg)"),
        BotCommand("authorize", "Admin: Authorize with PIN"),
        BotCommand("dashboard", "Admin: System overview"),
        BotCommand("users", "Admin: View all users"),
        BotCommand("invite", "Admin: Generate invite link"),
        BotCommand("healthcheck", "Admin: Check system health"),
        BotCommand("logs", "Admin: View audit logs"),
        BotCommand("journal", "View recent trade signals"),
        BotCommand("expectancy", "View system performance stats"),
    ]
    await app.bot.set_my_commands(commands)
    logger.info("Bot commands registered (14 total)")
    
    logger.info("TITAN V1 ONLINE")
    async with app:
        await app.initialize()
        await app.start()
        await app.updater.start_polling(
            drop_pending_updates=True,
            allowed_updates=["message","callback_query"]
        )
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(run())
