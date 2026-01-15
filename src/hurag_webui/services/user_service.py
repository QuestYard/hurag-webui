from .. import dbs, logger, conf, generate_id
from ..models import User

async def get_user(account: str) -> User | None:
    resp = await dbs.query(
        "SELECT id, account, username, user_path FROM users WHERE account = %s",
        (account,),
    )
    return User().from_db_response(resp[0]) if resp else None


async def get_user_by_id(id: str) -> User | None:
    resp = await dbs.query(
        "SELECT id, account, username, user_path FROM users WHERE id = %s", (id,)
    )
    return User().from_db_response(resp[0]) if resp else None


async def is_account_exist(account: str) -> bool:
    resp = await dbs.query("SELECT 1 FROM users WHERE account = %s", (account,))
    return bool(resp)


async def is_user_id_exist(user_id: str) -> bool:
    resp = await dbs.query("SELECT 1 FROM users WHERE id = %s", (user_id,))
    return bool(resp)


async def is_user_valid(user_id: str, account: str) -> bool:
    resp = await dbs.query(
        "SELECT 1 FROM users WHERE id = %s AND account = %s", (user_id, account)
    )
    return bool(resp)


async def upsert_user(account, username, user_path) -> User | None:
    resp = await dbs.dml(
        """
        INSERT INTO users (id, account, username, user_path)
        VALUES (%s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            username = VALUES(username),
            user_path = VALUES(user_path)
        """,
        (generate_id(), account, username, user_path),
    )
    return await get_user(account)


async def login(account: str):
    sso_info = None
    if conf.services.sso is not None:
        # should change to real sso service later
        logger.error("SSO is unavailable, login failed.")
    else:
        import csv
        from pathlib import Path

        with open(Path.cwd() / "native_sso.csv", "r", encoding="utf-8") as f:
            csv_reader = csv.DictReader(f)
            for row in csv_reader:
                if row["account"] == account:
                    sso_info = row.copy()
                    break

    if sso_info is not None:
        user = await upsert_user(**sso_info)
        return user

    return None
