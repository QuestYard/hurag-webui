import mariadb

from functools import lru_cache
from uuid6 import uuid7
from ..kernel import conf

@lru_cache
def _pool():
    cnf = conf()
    conn_pool = mariadb.ConnectionPool(
        pool_name="hurag2_webui_rss",
        host=cnf.mariadb.host,
        port=cnf.mariadb.port,
        user=cnf.mariadb.user,
        password=cnf.mariadb.password,
        database=cnf.mariadb.database,
    )
    return conn_pool

def query(statement, data=()):
    with (
        _pool().get_connection() as conn,
        conn.cursor() as cur
    ):
        cur.execute(statement, data)
        return cur.fetchall()

def dml(statement, data=())-> int:
    with (
        _pool().get_connection() as conn,
        conn.cursor() as cur
    ):
        try:
            if data is not None and isinstance(data, list):
                cur.executemany(statement, data)
            else:
                cur.execute(statement, data or ())
            conn.commit()
            return cur.rowcount
        except Exception as e:
            conn.rollback()
            raise e

def transact(statements, data):
    with (
        _pool().get_connection() as conn,
        conn.cursor() as cur
    ):
        try:
            for st, dt in zip(statements, data):
                if dt is not None and isinstance(dt, list):
                    cur.executemany(st, dt)
                else:
                    cur.execute(st, dt or ())
            conn.commit()
        except Exception as e:
            conn.rollback()
            raise e

_INIT_RSS_SCRIPTS = [
    "DROP TABLE IF EXISTS query_segments",
    "DROP TABLE IF EXISTS session_messages",
    "DROP TABLE IF EXISTS sessions",
    "DROP TABLE IF EXISTS users",
    """
    CREATE TABLE users (
        id UUID PRIMARY KEY,
        account VARCHAR(20) UNIQUE NOT NULL,
        username VARCHAR(50) NOT NULL,
        user_path VARCHAR(100) NOT NULL
    );""",
    """
    CREATE TABLE sessions (
        id UUID PRIMARY KEY,
        title VARCHAR(100) NOT NULL,
        created_ts TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
        user_id UUID NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
        INDEX idx_title (title),
        INDEX idx_ts (created_ts)
    );""",
    """
    CREATE TABLE session_messages (
        id UUID PRIMARY KEY,
        session_id UUID NOT NULL,
        seq_no INT NOT NULL,
        role VARCHAR(20) NOT NULL,
        content TEXT NOT NULL,
        created_ts TIMESTAMP(6) NOT NULL DEFAULT CURRENT_TIMESTAMP,
        likes INT NOT NULL DEFAULT 0,
        dislikes INT NOT NULL DEFAULT 0,
        pair_id UUID NOT NULL,
        FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE,
        INDEX idx_session (session_id),
        INDEX idx_ts (created_ts)
    );""",
    """
    CREATE TABLE query_segments (
        query_id UUID NOT NULL,
        segment_id UUID NOT NULL,
        seq_no INT NOT NULL,
        PRIMARY KEY (query_id, segment_id),
        FOREIGN KEY (query_id) REFERENCES session_messages(id) ON DELETE CASCADE
    );""",
]

def init_rss():
    data = [()] * len(_INIT_RSS_SCRIPTS)
    transact(_INIT_RSS_SCRIPTS, data)
    dml(
        f"""
        INSERT INTO users (id, account, username, user_path)
        VALUES (?, ?, ?, ?)
        """,
        [
            (
                uuid7(),
                'hurag',
                'HuRAG项目组',
                '/国家局（总公司）/浙江省局（公司）/湖州市局（公司）'
            ),
        ]
    )


