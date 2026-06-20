from db.database import execute_write, execute_read_one
import logging

logger = logging.getLogger(__name__)

async def run_migrations():
    logger.info("Running database migrations...")
    await create_users_table()
    await create_audit_logs_table()
    logger.info("Database migrations completed.")

async def create_users_table():
    query = """
    CREATE TABLE IF NOT EXISTS users (
        telegram_id INTEGER PRIMARY KEY,
        username TEXT,
        first_name TEXT,
        last_name TEXT,
        state TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    await execute_write(query)
    logger.info("Users table ensured.")

async def create_audit_logs_table():
    query = """
    CREATE TABLE IF NOT EXISTS audit_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        level TEXT NOT NULL,
        message TEXT NOT NULL,
        context TEXT
    );
    """
    await execute_write(query)
    logger.info("Audit logs table ensured.")
