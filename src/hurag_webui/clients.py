import asyncio
import threading

class LifespanClient:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._shutdown_event = None  # Will be created on first shutdown
        self.model = None
        self.client = None

    @property
    def started(self) -> bool:
        with self._lock:
            return self.client is not None

    def startup(self, base_url, api_key, model):
        from hurag.llm import create_client
        with self._lock:
            # Check if shutdown is in progress
            if self._shutdown_event is not None and not self._shutdown_event.is_set():
                raise RuntimeError("Cannot start client while shutdown is in progress")
            # Safe to reset - if event exists, it's already set and all waiters have been notified
            # The asyncio.Event.wait() returns immediately for all waiters once set() is called
            self._shutdown_event = None
            self.model = model
            self.client = create_client(base_url=base_url, api_key=api_key)

    async def shutdown(self):
        client_to_close = None
        shutdown_event = None
        should_shutdown = False
        
        with self._lock:
            # Check if shutdown is already in progress
            if self._shutdown_event is not None and not self._shutdown_event.is_set():
                # Wait for the ongoing shutdown
                shutdown_event = self._shutdown_event
            elif self.client is not None:
                # We need to perform the shutdown
                should_shutdown = True
                shutdown_event = asyncio.Event()
                self._shutdown_event = shutdown_event
                self.model = None
                client_to_close = self.client
                self.client = None
            else:
                # No client and no shutdown in progress - nothing to do
                return
        
        # If we're waiting for an existing shutdown, do so outside the lock
        if not should_shutdown:
            await shutdown_event.wait()
            return
        
        # Perform the actual shutdown outside the lock
        try:
            await client_to_close.close()
        finally:
            shutdown_event.set()

# Global lifespan chat completions client
chat_client = LifespanClient()
