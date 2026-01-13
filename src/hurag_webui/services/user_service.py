from ..dss import rss
from ..models import User
from ..kernel import logger, conf

from uuid6 import uuid7

def get_user(account: str)-> User|None:
    resp = rss.query(
        """
        SELECT id, account, username, user_path
        FROM users
        WHERE account = ?
        """,
        (account, ),
    )
    return User().from_db_response(resp[0]) if resp else None

def get_user_by_id(id: str)-> User|None:
    resp = rss.query(
        """
        SELECT id, account, username, user_path
        FROM users
        WHERE id = ?
        """,
        (id, ),
    )
    return User().from_db_response(resp[0]) if resp else None

def is_account_exist(account: str)-> bool:
    resp = rss.query(
        """
        SELECT 1
        FROM users
        WHERE account = ?
        """,
        account,
    )
    return bool(resp)

def is_user_id_exist(user_id: str)-> bool:
    resp = rss.query(
        """
        SELECT 1
        FROM users
        WHERE id = ?
        """,
        user_id,
    )
    return bool(resp)

def is_user_valid(user_id: str, account: str)-> bool:
    resp = rss.query(
        """
        SELECT 1
        FROM users
        WHERE id = ? AND account = ?
        """,
        (user_id, account),
    )
    return bool(resp)

def upsert_user(account, username, user_path)-> User|None:
    resp = rss.dml(
        """
        INSERT INTO users (id, account, username, user_path)
        VALUES (?, ?, ?, ?)
        ON DUPLICATE KEY UPDATE
            username = VALUES(username),
            user_path = VALUES(user_path)
        """,
        (uuid7(), account, username, user_path)
    )
    return get_user(account)

def login(account: str):
    sso_info = None
    if conf().api.sso is not None:
        # should change to real sso service later
        logger.error("SSO is unavailable, login failed.", type="negative")
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
        user = upsert_user(**sso_info)
        return user

    return None



