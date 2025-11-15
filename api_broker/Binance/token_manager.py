import os
import psycopg2
from psycopg2.extras import RealDictCursor

DB_HOST = os.environ.get("DB_HOST")
DB_ID = os.environ.get("DB_ID")
DB_NAME = "tedb"
DB_ROOT_CA_PATH = os.environ.get("DB_ROOT_CA_PATH")
DB_CERT_PATH = os.environ.get("DB_CERT_PATH")
DB_CERT_KEY_PATH = os.environ.get("DB_CERT_KEY_PATH")

def get_db_conn():
    return psycopg2.connect(
        host=DB_HOST,
        database=DB_NAME,
        user=DB_ID,
        cursor_factory=RealDictCursor,
        sslmode='verify-full',
        sslrootcert=DB_ROOT_CA_PATH,
        sslcert=DB_CERT_PATH,       
        sslkey=DB_CERT_KEY_PATH,
    )

def get_tokens():
    conn = get_db_conn()
    
    return