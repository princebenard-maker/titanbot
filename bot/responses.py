WELCOME_MESSAGE = """
Welcome to TITAN V1!

I'm your AI-assisted crypto trading system. I help you grow your crypto portfolio through disciplined, rule-based trading on Binance Futures.

To get started, an admin needs to approve your account. Please wait for approval.
"""

WELCOME_ADMIN_MESSAGE = """
Welcome, Admin!

You have full control over TITAN V1. Use /authorize <PIN> to log in.
"""

ADMIN_AUTHORIZED_MESSAGE = "You are now authorized as Admin."
ADMIN_UNAUTHORIZED_MESSAGE = "Invalid PIN or not an admin. Access denied."
ADMIN_ALREADY_AUTHORIZED_MESSAGE = "You are already authorized as Admin."

NOT_AUTHORIZED_MESSAGE = "You are not authorized to use this command."

USER_PENDING_APPROVAL_MESSAGE = "Your account is pending approval. Please wait for an admin to approve you."
USER_REJECTED_MESSAGE = "Your account has been rejected by the admin."
USER_PAUSED_MESSAGE = "Your account is currently paused. Please contact an admin."
USER_SUSPENDED_MESSAGE = "Your account has been suspended. Please contact an admin."

DASHBOARD_MESSAGE = """
📊 *ADMIN DASHBOARD* 📊

*System Status*: Operational
*Active Users*: {active_users}
*Pending Users*: {pending_users}
*Total Users*: {total_users}
"""

USERS_LIST_MESSAGE = """
👥 *TITAN Users* 👥

{user_list}
"""

NO_USERS_MESSAGE = "No users found."

INVITE_MESSAGE = "Invite link generated: {invite_link}"

HEALTHCHECK_MESSAGE = """
💚 *TITAN Healthcheck* 💚

*Database*: OK
*Telegram Bot*: OK
*Last Audit Log*: {last_audit_log}
"""

NO_AUDIT_LOGS_MESSAGE = "No audit logs found."

AUDIT_LOGS_MESSAGE = """
📜 *Latest Audit Logs* 📜

{logs}
"""

INVALID_COMMAND_MESSAGE = "Invalid command."
