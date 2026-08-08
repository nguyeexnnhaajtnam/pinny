import asyncpg

from pinny.core.config import Settings


async def check_database(settings: Settings) -> None:
    connection = await asyncpg.connect(
        host=settings.database_host,
        port=settings.database_port,
        database=settings.database_name,
        user=settings.database_user,
        password=settings.database_password,
        timeout=settings.database_connect_timeout,
    )
    try:
        await connection.execute("SELECT 1")
    finally:
        await connection.close()
