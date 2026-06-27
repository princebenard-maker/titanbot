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
    
    # Initialize Wave 2C/2D components
    from core.state_manager import initialize_state
    from core.health_monitor import get_health_monitor
    from core.recovery_engine import get_recovery_engine
    
    await initialize_state()
    logger.info("State manager initialized")
    
    recovery_engine = get_recovery_engine()
    await recovery_engine.initialize()
    logger.info("Recovery engine initialized")
    
    health_monitor = get_health_monitor()
    await health_monitor.start()
    logger.info("Health monitor started")
    
    from telegram.ext import ApplicationBuilder, MessageHandler, filters
    from bot.handlers.start import register_start
    from bot.handlers.admin import register_admin
    from bot.handlers.signals import register_signals
    from bot.handlers.journal import register_journal
    from bot.handlers.operations import register_operations
    from bot.handlers.conversational import get_conversational_engine
    from bot.handlers.paper import register_paper
    app = ApplicationBuilder().token(token).build()
    register_start(app)
    register_admin(app)
    register_signals(app)
    register_journal(app)
    register_operations(app)
    register_paper(app)
    
    # Initialize Wave 3A paper broker
    from broker.paper import get_paper_broker
    paper_broker = get_paper_broker()
    await paper_broker.connect()
    logger.info("Paper broker connected")
    
    # Conversational handler - processes natural language
    conv_engine = get_conversational_engine()
    
    async def handle_text(update, context):
        """Handle free-form text messages."""
        text = update.message.text.strip()
        user_id = update.effective_user.id
        
        # Ignore commands
        if text.startswith('/'):
            return
        
        # Process conversationally
        response = await conv_engine.process(text, user_id)
        await update.message.reply_text(response)
    
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    logger.info("Conversational handler registered")
    
    # Set bot commands in Telegram menu
    commands = [
        BotCommand("start", "Welcome to Titan V1"),
        BotCommand("help", "View all commands"),
        BotCommand("status", "Check your account status"),
        BotCommand("signal", "Generate trade signal (pair arg)"),
        BotCommand("regime", "Check market regime (pair arg)"),
        BotCommand("score", "View confidence breakdown (pair arg)"),
        BotCommand("journal", "View recent trade signals"),
        BotCommand("expectancy", "View system performance stats"),
        # Learning commands
        BotCommand("weekly_review", "Weekly performance review"),
        BotCommand("calibration", "Confidence calibration analysis"),
        BotCommand("feature_importance", "Feature importance analysis"),
        BotCommand("explain", "Explain signal decision (ID arg)"),
        # Operational commands
        BotCommand("health", "Quick health check"),
        BotCommand("health_report", "Full health report"),
        BotCommand("system_state", "View system state"),
        BotCommand("recovery", "View recovery sessions"),
        BotCommand("diagnostics", "Full diagnostic report"),
        # Admin commands
        BotCommand("authorize", "Admin: Authorize with PIN"),
        BotCommand("dashboard", "Admin: System overview"),
        BotCommand("users", "Admin: View all users"),
        BotCommand("pending", "Admin: View pending users"),
        BotCommand("approve", "Admin: Approve user by ID"),
        BotCommand("reject", "Admin: Reject user by ID"),
        BotCommand("suspend", "Admin: Suspend user by ID"),
        BotCommand("resume", "Admin: Resume user by ID"),
        BotCommand("classify", "Admin: Classify failure (ID type)"),
        BotCommand("risk", "Admin: View risk settings"),
        BotCommand("enable_trading", "Admin: Enable trading"),
        BotCommand("disable_trading", "Admin: Disable trading"),
        BotCommand("invite", "Admin: Generate invite link"),
        BotCommand("healthcheck", "Admin: Check system health"),
        BotCommand("logs", "Admin: View audit logs"),
        # Paper trading commands
        BotCommand("account", "Paper account status"),
        BotCommand("positions", "View open positions"),
        BotCommand("history", "Trade history"),
        BotCommand("paper_report", "Paper trading report"),
        BotCommand("broker", "Current broker status"),
    ]
    await app.bot.set_my_commands(commands)
    logger.info("Bot commands registered (36 total)")
    
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
