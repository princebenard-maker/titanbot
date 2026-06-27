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
    await create_paper_tables()  # Wave 3A
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


async def create_paper_tables():
    """Create paper trading tables."""
    
    # Paper account table
    await execute_write("""
        CREATE TABLE IF NOT EXISTS paper_account (
            id INTEGER PRIMARY KEY,
            broker TEXT NOT NULL DEFAULT 'PAPER',
            initial_balance REAL NOT NULL DEFAULT 10.0,
            balance REAL NOT NULL DEFAULT 10.0,
            equity REAL NOT NULL DEFAULT 10.0,
            available_balance REAL NOT NULL DEFAULT 10.0,
            reserved REAL DEFAULT 0.0,
            realized_pnl REAL DEFAULT 0.0,
            unrealized_pnl REAL DEFAULT 0.0,
            peak_equity REAL DEFAULT 10.0,
            max_drawdown REAL DEFAULT 0.0,
            daily_loss REAL DEFAULT 0.0,
            weekly_loss REAL DEFAULT 0.0,
            total_trades INTEGER DEFAULT 0,
            winning_trades INTEGER DEFAULT 0,
            losing_trades INTEGER DEFAULT 0,
            breakeven_trades INTEGER DEFAULT 0,
            win_rate REAL DEFAULT 0.0,
            profit_factor REAL DEFAULT 0.0,
            avg_win REAL DEFAULT 0.0,
            avg_loss REAL DEFAULT 0.0,
            expectancy REAL DEFAULT 0.0,
            consecutive_wins INTEGER DEFAULT 0,
            consecutive_losses INTEGER DEFAULT 0,
            max_win_streak INTEGER DEFAULT 0,
            max_loss_streak INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    logger.info("Paper account table ensured.")
    
    # Paper positions table
    await execute_write("""
        CREATE TABLE IF NOT EXISTS paper_positions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            trade_id TEXT UNIQUE,
            signal_id INTEGER,
            pair TEXT NOT NULL,
            side TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'OPEN',
            entry_price REAL NOT NULL,
            quantity REAL NOT NULL,
            entry_time TIMESTAMP,
            exit_price REAL,
            exit_time TIMESTAMP,
            exit_reason TEXT,
            stop_loss REAL NOT NULL,
            take_profit REAL NOT NULL,
            risk_percent REAL DEFAULT 2.0,
            risk_amount REAL DEFAULT 0.0,
            position_size REAL DEFAULT 0.0,
            pnl REAL DEFAULT 0.0,
            pnl_percent REAL DEFAULT 0.0,
            r_multiple REAL DEFAULT 0.0,
            setup_type TEXT DEFAULT 'N/A',
            regime TEXT DEFAULT 'UNKNOWN',
            confidence INTEGER DEFAULT 0,
            duration_hours REAL DEFAULT 0.0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    logger.info("Paper positions table ensured.")
    
    # Create indexes
    await execute_write("CREATE INDEX IF NOT EXISTS idx_paper_positions_pair ON paper_positions(pair)")
    await execute_write("CREATE INDEX IF NOT EXISTS idx_paper_positions_status ON paper_positions(status)")
    await execute_write("CREATE INDEX IF NOT EXISTS idx_paper_positions_signal ON paper_positions(signal_id)")
