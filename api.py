import os
# Session configuration
session_service = DatabaseSessionService(db_url=os.environ.get("DB_URL"))