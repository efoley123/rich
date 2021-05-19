from functools import total_ordering
from typing import AsyncIterable, Optional, NamedTuple, Tuple, TYPE_CHECKING
import asyncio
from asyncio import ensure_future, Task, PriorityQueue
from asyncio import Event as AIOEvent
from dataclasses import dataclass
from functools import total_ordering
import logging

from . import events
from .message import Message
from ._timer import Timer, TimerCallback
from .types import MessageTarget, MessageHandler

log = logging.getLogger("rich")


@total_ordering
class MessageQueueItem(NamedTuple):
    priority: int
    message: Message

    def __gt__(self, other: "MessageQueueItem") -> bool:
        return self.priority > other.priority

    def __eq__(self, other: "MessageQueueItem") -> bool:
        return self.priority == other.priority


class MessagePumpClosed(Exception):
    pass


class MessagePump:
    def __init__(
        self, queue_size: int = 10, parent: Optional["MessagePump"] = None
    ) -> None:
        self._message_queue: "PriorityQueue[Optional[MessageQueueItem]]" = (
            PriorityQueue(queue_size)
        )
        self._parent = parent
        self._closing: bool = False
        self._closed: bool = False

    async def get_message(self) -> MessageQueueItem:
        """Get the next event on the queue, or None if queue is closed.

        Returns:
            Optional[Event]: Event object or None.
        """
        if self._closed:
            raise MessagePumpClosed("The message pump is closed")
        queue_item = await self._message_queue.get()
        if queue_item is None:
            self._closed = True
            raise MessagePumpClosed("The message pump is now closed")
        return queue_item

    def set_timer(
        self,
        delay: float,
        *,
        name: Optional[str] = None,
        callback: TimerCallback = None,
    ) -> Timer:
        timer = Timer(self, delay, self, name=name, callback=callback, repeat=0)
        asyncio.get_event_loop().create_task(timer.run())
        return timer

    def set_interval(
        self,
        interval: float,
        *,
        name: Optional[str] = None,
        callback: TimerCallback = None,
        repeat: int = 0,
    ):
        timer = Timer(
            self, interval, self, name=name, callback=callback, repeat=repeat or None
        )
        asyncio.get_event_loop().create_task(timer.run())
        return timer

    async def close_messages(self) -> None:
        self._closing = True
        await self._message_queue.put(None)

    async def process_messages(self) -> None:

        while not self._closed:
            try:
                priority, message = await self.get_message()
            except MessagePumpClosed:
                log.exception("error getting message")
                break
            log.debug("message=%r", message)
            await self.dispatch_message(message, priority)

    async def dispatch_message(self, message: Message, priority: int) -> Optional[bool]:
        if isinstance(message, events.Event):
            method_name = f"on_{message.name}"
            dispatch_function: MessageHandler = getattr(self, method_name, None)
            if dispatch_function is not None:
                await dispatch_function(message)
            if message.bubble and self._parent:
                await self._parent.post_message(message, priority)
        else:
            return await self.on_message(message)
        return False

    async def on_message(self, message: Message) -> None:
        pass

    async def post_message(
        self,
        message: Message,
        priority: Optional[int] = None,
    ) -> bool:
        if self._closing or self._closed:
            return False
        event_priority = priority if priority is not None else message.default_priority
        item = MessageQueueItem(event_priority, message)
        await self._message_queue.put(item)
        return True

    async def emit(self, message: Message, priority: Optional[int] = None) -> None:
        if self._parent:
            await self._parent.post_message(message, priority=priority)

    async def on_timer(self, event: events.Timer) -> None:
        if event.callback is not None:
            await event.callback(event)


if __name__ == "__main__":

    class Widget(MessagePump):
        pass

    widget1 = Widget()
    widget2 = Widget()

    import asyncio

    asyncio.get_event_loop().run_until_complete(widget1.run_message_loop())