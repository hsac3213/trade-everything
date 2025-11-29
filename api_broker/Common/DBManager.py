from Common.Debug import *
import psycopg2
from psycopg2 import pool
from psycopg2.extras import RealDictCursor
import os

# DB 서버 관련 환경변수 읽기
DB_HOST= os.environ.get("DB_HOST")
DB_ID = os.environ.get("DB_ID")
DB_NAME = "tedb"
DB_ROOT_CA_PATH = os.environ.get("DB_ROOT_CA_PATH")
DB_CERT_PATH = os.environ.get("DB_CERT_PATH")
DB_CERT_KEY_PATH = os.environ.get("DB_CERT_KEY_PATH")

DB_MIN_CONN = 1
DB_MAX_CONN = 100

_db_pool = None

def init_db_pool():
    global _db_pool
    if _db_pool is None:
        try:
            _db_pool = pool.ThreadedConnectionPool(
                minconn=DB_MIN_CONN,
                maxconn=DB_MAX_CONN,
                host=DB_HOST,
                database=DB_NAME,
                user=DB_ID,
                cursor_factory=RealDictCursor,
                sslmode='verify-full',
                sslrootcert=DB_ROOT_CA_PATH,
                sslcert=DB_CERT_PATH,       
                sslkey=DB_CERT_KEY_PATH,
            )
            print("DB Pool Initialized.")
        except Exception as e:
            Error(f"{e}")

class PooledConnection:
    def __init__(self, pool, conn):
        self._pool = pool
        self._conn = conn
        self._closed = False

    def close(self):
        if not self._closed and self._conn:
            # 연결을 닫지 않고 Pool에 반환
            self._pool.putconn(self._conn)
            self._closed = True
            self._conn = None

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        print("DB Pool Closed!")
        self.close()

    def __getattr__(self, name):
        # 그 외 모든 속성/메서드는 원본 연결 객체로 전달
        return getattr(self._conn, name)

def get_db_conn():
    global _db_pool
    if _db_pool is None:
        init_db_pool()
    
    if _db_pool:
        try:
            conn = _db_pool.getconn()
            if conn:
                return PooledConnection(_db_pool, conn)
        except Exception as e:
            Error(f"{e}")
    
    return None

class DBManager:
    def __init__(self):
        self.conn = None

    def connect(self):
        self.conn = psycopg2.connect(
            host=DB_HOST,
            database=DB_NAME,
            user=DB_ID,
            cursor_factory=RealDictCursor,
            sslmode='verify-full',
            sslrootcert=DB_ROOT_CA_PATH,
            sslcert=DB_CERT_PATH,       
            sslkey=DB_CERT_KEY_PATH,
        )

    def close(self):
        if self.conn and not self.conn.closed:
            self.conn.close()

    def get_conn(self):
        if self.conn is None or self.conn.closed:
            self.connect()
        return self.conn