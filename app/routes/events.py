from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
from datetime import datetime

events_router = APIRouter(prefix="/agent", tags=["events"])

_message_subscribers: list[dict] = []
_message_history: list[dict] = []
MAX_HISTORY = 100


def broadcast_message(msg_type: str, lineage_id: str, content: str, data: dict | None = None):
    msg = {
        "type": msg_type,
        "lineage_id": lineage_id,
        "content": content,
        "data": data or {},
        "timestamp": int(datetime.now().timestamp() * 1000),
    }
    _message_history.append(msg)
    if len(_message_history) > MAX_HISTORY:
        _message_history.pop(0)

    for subscriber in _message_subscribers:
        try:
            subscriber["queue"].put_nowait(msg)
        except:
            pass


@events_router.get("/events/subscribe")
async def subscribe_events():
    queue = asyncio.Queue()
    subscriber = {"queue": queue}
    _message_subscribers.append(subscriber)

    async def event_generator():
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30)
                    import json

                    yield f"data: {json.dumps(msg)}\n\n"
                except asyncio.TimeoutError:
                    ts = int(datetime.now().timestamp() * 1000)
                    ping_msg = f"data: {{'type': 'ping', 'timestamp': {ts}}}\n\n"
                    yield ping_msg
        finally:
            _message_subscribers.remove(subscriber)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@events_router.get("/events/history")
async def get_message_history(limit: int = 50):
    return {
        "messages": _message_history[-limit:] if _message_history else [],
        "total": len(_message_history),
    }
