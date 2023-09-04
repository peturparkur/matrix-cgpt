from typing import AsyncGenerator, Any, AsyncIterator, Generator, Optional
import nio
import simplematrixbotlib as botlib

async def recursive_message(bot: botlib.Bot, room: nio.rooms.MatrixRoom, n: int = 100, batch: int = 10, start: str = "") -> AsyncGenerator[tuple[Optional[nio.RoomMessagesError], Optional[nio.BadEventType | nio.Event]], Any]:
    assert batch <= n
    m = n
    while(m > 0):
        history: nio.RoomMessagesResponse | nio.RoomMessagesError = await bot.api.async_client.room_messages(
            room.room_id, 
            start=start, 
            limit=min(batch, m), 
            direction=nio.MessageDirection.back
        )
        if not isinstance(history, nio.RoomMessagesError):
            for x in history.chunk:
                yield  (None, x) # type: ignore
            start = history.end
        else:
            yield (history, None) # type: ignore
            break