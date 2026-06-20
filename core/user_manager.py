from db.database import execute_write, execute_read_one, execute_read
from config.constants import (
    USER_STATE_PENDING_APPROVAL,
    USER_STATE_ACTIVE,
    USER_STATE_PAUSED,
    USER_STATE_SUSPENDED,
    USER_STATE_REJECTED,
    ADMIN_TELEGRAM_ID
)
import logging

logger = logging.getLogger(__name__)

async def get_or_create_user(telegram_id, username, first_name, last_name):
    user = await execute_read_one(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    )
    if user:
        return user
    
    state = USER_STATE_PENDING_APPROVAL
    if telegram_id == ADMIN_TELEGRAM_ID:
        state = USER_STATE_ACTIVE # Admin is automatically active

    await execute_write(
        "INSERT INTO users (telegram_id, username, first_name, last_name, state) VALUES (?, ?, ?, ?, ?)",
        (telegram_id, username, first_name, last_name, state),
    )
    logger.info(f"New user {telegram_id} created with state {state}")
    return await execute_read_one(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    )

async def get_user(telegram_id):
    return await execute_read_one(
        "SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)
    )

async def update_user_state(telegram_id, state):
    await execute_write(
        "UPDATE users SET state = ?, updated_at = CURRENT_TIMESTAMP WHERE telegram_id = ?",
        (state, telegram_id),
    )
    logger.info(f"User {telegram_id} state updated to {state}")

async def is_admin(telegram_id):
    return telegram_id == ADMIN_TELEGRAM_ID

async def get_all_users():
    return await execute_read("SELECT * FROM users")
