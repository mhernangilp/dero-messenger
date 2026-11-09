"""Polling with bounded backoff; no automatic paid retries."""

import time
from collections.abc import Callable

from .conversations import Messenger
from .rpc import RPCError


def listen(messenger: Messenger, display: Callable[[str], None], interval: float = 5) -> None:
    delay = interval
    while True:
        try:
            for event in messenger.sync():
                display(event)
            delay = interval
        except RPCError:
            display("Wallet unavailable; synchronization will retry")
            delay = min(delay * 2, 60)
        time.sleep(delay)
