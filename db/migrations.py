from db.database import execute_write, execute_read_one
import logging
import os

logger = logging.getLogger(__name__)

async def run_migrations():
    logger.info("Running database migrations...")
    await create_users_table()
    await create_audit_logs_table()
    await create_signals_table()
    await create_expectancy_log_table()
    await add_setup_type_column()
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

async def create_signals_table():
    await execute_write("""
        CREATE TABLE IF NOT EXISTS signals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            symbol TEXT NOT NULL,
            signal TEXT NOT NULL,
            score INTEGER NOT NULL,
            regime TEXT NOT NULL,
            score_breakdown TEXT,
            entry_price REAL DEFAULT 0.0,
            outcome TEXT DEFAULT 'PENDING',
            exit_price REAL DEFAULT 0.0,
            pnl_pct REAL DEFAULT 0.0
        )
    """)
    logger.info("Signals table ensured.")

async def create_expectancy_log_table():
    await execute_write("""
        CREATE TABLE IF NOT EXISTS expectancy_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            band TEXT NOT NULL,
            total_signals INTEGER DEFAULT 0,
            win_rate REAL DEFAULT 0.0,
            expectancy REAL DEFAULT 0.0
        )
    """)
    logger.info("Expectancy log table ensured.")

async def add_setup_type_column():
    """Add setup_type column to signals table if it doesn't exist."""
    from db.database import execute_read_one
    # Check if column exists
    result = await execute_read_one("PRAGMA table_info(signals)")
    if result:
        # Check all columns
        import sqlite3
        conn = sqlite3.connect(os.getenv("DB_PATH", "./data/titanbot.db"))
        cursor = conn.execute("PRAGMA table_info(signals)")
        columns = [row[1] for row in cursor.fetchall()]
        conn.close()
        
        if 'setup_type' not in columns:
            await execute_write("""
                ALTER TABLE signals ADD COLUMN setup_type TEXT DEFAULT 'N/A'
            """)
            logger.info("Added setup_type column to signals table.")
        else:
            logger.info("setup_type column already exists.")
