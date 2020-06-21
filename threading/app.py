from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from random import randint
from threading import Lock, Thread

from psycopg2.pool import SimpleConnectionPool

CACHE = b"1234567890abcde" * 64 * 1024 * 256  # Assume each worker will have a 256MB cache
POOL = None
POOL_LOCK = Lock()
POOL_SIZE = 3
THREAD_POOL = ThreadPoolExecutor(POOL_SIZE)

@contextmanager
def get_conn():
    global POOL
    with POOL_LOCK:
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
        try:
            resp = cur.fetchone()[0]
        except:
            resp = ""
        cur.close()
    return resp

def view(receive):
    future = THREAD_POOL.submit(insert, receive)
    body = select()
    future.result()
    return "200 OK", body

def request(receive):
    return receive().decode('utf-8')

def response(send, status, body):
    send(status, [('Content-Type','application/json')])
    return [body.encode("utf-8")]

def app(env, send):
    return response(send, *view(lambda : env['wsgi.input'].read(int(env['CONTENT_LENGTH']))))
