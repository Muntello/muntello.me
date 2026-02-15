from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text
from app.config import settings
from app.models import Base
import logging


logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(
    settings.DATABASE_URL if settings else "sqlite+aiosqlite:///:memory:",
    echo=settings.DEBUG if settings else False,
    future=True
)

# Create async session factory
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def init_db():
    """Initialize database tables and apply migrations"""
    logger.info("Initializing database tables")
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables created successfully")
    await _migrate_db()


async def _get_table_columns(conn, table_name: str) -> set[str]:
    """Get column names for a table via PRAGMA table_info."""
    result = await conn.execute(text(f"PRAGMA table_info('{table_name}')"))
    return {row[1] for row in result.fetchall()}


async def _add_column_if_missing(conn, table: str, column: str, definition: str):
    """Add a column to a table if it doesn't already exist."""
    cols = await _get_table_columns(conn, table)
    if column not in cols:
        await conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {column} {definition}"))
        logger.info(f"Added column {table}.{column}")


async def _migrate_db():
    """Apply schema migrations for existing databases.

    create_all() only creates missing tables, not missing columns.
    Each column is checked individually so partial migrations are safe.
    """
    async with engine.begin() as conn:
        # Messages table: dual IDs and content fields
        await _add_column_if_missing(conn, "messages", "user_chat_message_id", "INTEGER")
        await _add_column_if_missing(conn, "messages", "support_chat_message_id", "INTEGER")
        await _add_column_if_missing(conn, "messages", "content_type", "VARCHAR(20) NOT NULL DEFAULT 'text'")
        await _add_column_if_missing(conn, "messages", "file_id", "VARCHAR(255)")

        # Backfill from legacy telegram_message_id (if it exists)
        msg_cols = await _get_table_columns(conn, "messages")
        if "telegram_message_id" in msg_cols:
            await conn.execute(text(
                "UPDATE messages SET user_chat_message_id = telegram_message_id "
                "WHERE is_from_user = 1 AND user_chat_message_id IS NULL"
            ))
            await conn.execute(text(
                "UPDATE messages SET support_chat_message_id = telegram_message_id "
                "WHERE is_from_user = 0 AND support_chat_message_id IS NULL"
            ))

        # Pending messages table: content fields
        await _add_column_if_missing(conn, "pending_messages", "content_type", "VARCHAR(20) NOT NULL DEFAULT 'text'")
        await _add_column_if_missing(conn, "pending_messages", "file_id", "VARCHAR(255)")

    logger.info("Database migrations completed")


async def get_session() -> AsyncSession:
    """Dependency to get database session"""
    async with async_session() as session:
        try:
            yield session
        finally:
            await session.close()
