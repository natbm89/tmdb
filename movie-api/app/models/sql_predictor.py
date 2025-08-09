import psycopg
from app.config import DB_CONFIG

def execute_sql(sql_query):
    with psycopg.connect(**DB_CONFIG) as conn:
        with conn.cursor() as cur:
            cur.execute(sql_query)
            try:
                rows = cur.fetchall()
            except Exception:
                rows = cur.fetchone()
    return rows