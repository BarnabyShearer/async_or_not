from asyncio import gather, Lock
from contextlib import asynccontextmanager

from asyncpg import create_pool

CACHE = b"1234567890abcde" * 64 * 1024 * 256  # Assume each worker will have a 256MB cache
POOL = None
POOL_LOCK = Lock()
POOL_SIZE = 10

@asynccontextmanager
async def get_conn():
    global POOL
    async with POOL_LOCK:
        if not POOL:
            POOL = await create_pool(min_size=POOL_SIZE, max_size=POOL_SIZE, max_queries=9e9)
    async with POOL.acquire() as conn:
        yield conn

async def insert(receive):
    async with get_conn() as conn:
        await conn.execute("INSERT INTO demo (data) VALUES($1)", await request(receive))

async def select():
    async with get_conn() as conn:
        return await conn.fetchval("SELECT data::text FROM demo ORDER BY id DESC LIMIT 1")

async def view(receive):
    _, body = await gather(
        insert(receive),
        select()
    )
    return 200, body

async def request(receive):
    body = b""
    more_body = True
    while more_body:
        message = await receive()
        body += message.get("body", b"")
        more_body = message.get("more_body", False)
    return body.decode("utf-8")

async def response(send, status, body):
    await gather(
        send({"type": "http.response.start", "status": status, "headers": [(b"content-type", b"application/json"),]}),
        send({"type": "http.response.body", "body": body.encode("utf-8"), "more_body": False,})
    )

async def app(scope, receive, send):
    assert scope["type"] == "http"
    await response(send, *await view(receive))
