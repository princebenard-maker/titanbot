from db.database import execute_write, execute_read
import logging

logger = logging.getLogger(__name__)

async def log_event(level, message, context=None):
    query = "INSERT INTO audit_logs (level, message, context) VALUES (?, ?, ?)"
    await execute_write(query, (level, message, context))
    logger.info(f"AUDIT [{level}]: {message} (Context: {context})")

async def get_latest_audit_logs(limit=20):
    query = "SELECT * FROM audit_logs ORDER BY timestamp DESC LIMIT ?"
    return await execute_read(query, (limit,))
