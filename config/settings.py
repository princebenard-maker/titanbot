import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_TELEGRAM_ID = int(os.getenv("ADMIN_TELEGRAM_ID"))
ADMIN_PIN_HASH = os.getenv("ADMIN_PIN_HASH")
DB_PATH = os.getenv("DB_PATH", "./data/titanbot.db")
