import psycopg2
from psycopg2.extras import RealDictCursor
import os

# DB 서버 관련 환경변수 읽기
DB_HOST= os.environ.get("DB_HOST")
DB_ID = os.environ.get("DB_ID")
DB_NAME = "tedb"
DB_ROOT_CA_PATH = os.environ.get("DB_ROOT_CA_PATH")
DB_CERT_PATH = os.environ.get("DB_CERT_PATH")
DB_CERT_KEY_PATH = os.environ.get("DB_CERT_KEY_PATH")

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