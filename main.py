import logging, os, sys, asyncio
from pathlib import Path
from dotenv import load_dotenv
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
    app = ApplicationBuilder().token(token).build()
    register_start(app)
    register_admin(app)
    logger.info("TITAN V1 ONLINE")
    async with app:
        await app.start()
        await app.updater.start_polling(
            drop_pending_updates=True
        )
        await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(run())
