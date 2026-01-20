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
            if self._shutdown_event is not None and not self._shutdown_event.is_set():
                raise RuntimeError("Cannot start client while shutdown is in progress")
            self._shutdown_event = None  # Reset for potential future shutdown
            self.model = model
            self.client = create_client(base_url=base_url, api_key=api_key)

    async def shutdown(self):
        shutdown_event = None
        client_to_close = None
        
        with self._lock:
            # If shutdown is already in progress, wait for it
            if self._shutdown_event is not None and not self._shutdown_event.is_set():
                shutdown_event = self._shutdown_event
            else:
                # Start a new shutdown
                self._shutdown_event = asyncio.Event()
                shutdown_event = self._shutdown_event
                self.model = None
                client_to_close = self.client
                self.client = None
        
        # If we're waiting for an existing shutdown, do so outside the lock
        if client_to_close is None:
            await shutdown_event.wait()
            return
        
        # Perform the actual shutdown outside the lock
        try:
            if client_to_close:
                await client_to_close.close()
        finally:
            shutdown_event.set()

# Global lifespan chat completions client
chat_client = LifespanClient()
