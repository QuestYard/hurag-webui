async def init_db(connection=None, cursor=None):
    ensure = input("初始化数据库将清空现有数据，请确认(Y/N): ")
    if ensure.strip().lower()[0] != "y":
        print("Bye!")
        return

    import warnings
    from aiomysql import Warning as mysql_warning
    warnings.filterwarnings("ignore", category=mysql_warning)
    from . import logger
    from .constants import INIT_RSS_SCRIPTS
    from .dbs import get_pool, close_pool

    pool = await get_pool()
    try:
        async with pool.acquire() as conn, conn.cursor() as cur:
            for stmt in INIT_RSS_SCRIPTS:
                if not stmt:
                    continue
                await cur.execute(stmt)
            await conn.commit()
            logger.info("HuRAG WebUI database is initialized.")
            print("HuRAG WebUI 数据库已初始化。")
    except Exception as e:
        await conn.rollback()
        logger.error(f"Error while initializing the database: {e!r}")
        print("初始化数据库失败，请查看日志。")
        raise e
    finally:
        await close_pool()

def main():
    import asyncio
    asyncio.run(init_db())

