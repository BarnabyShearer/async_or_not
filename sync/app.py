from contextlib import contextmanager
from random import randint

from psycopg2.pool import SimpleConnectionPool

CACHE = b"1234567890abcde" * 64 * 1024 * 256  # Assume each worker will have a 256MB cache
POOL = None
POOL_SIZE = 5

@contextmanager
def get_conn():
    global POOL
    if not POOL:
        POOL = SimpleConnectionPool(POOL_SIZE, POOL_SIZE, "")
    conn = POOL.getconn()
    try:
        yield conn
    finally:
        POOL.putconn(conn)

def insert(receive):
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("INSERT INTO demo (data) VALUES(%s)", (request(receive),))
        cur.close()
        conn.commit()

def select():
    with get_conn() as conn:
        cur = conn.cursor()
        cur.execute("SELECT data::text FROM demo ORDER BY id DESC LIMIT 1")
        resp = cur.fetchone()[0]
        cur.close()
    return resp

def view(receive):
    insert(receive)
    body = select()
    return "200 OK", body

def request(receive):
    return receive().decode('utf-8')

def response(send, status, body):
    send(status, [('Content-Type','application/json')])
    return [body.encode("utf-8")]

def app(env, send):
    return response(send, *view(lambda : env['wsgi.input'].read(int(env['CONTENT_LENGTH']))))
