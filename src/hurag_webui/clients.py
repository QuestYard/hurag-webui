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
            # It's safe to reset now - either no shutdown event exists, or it's already complete
            self._shutdown_event = None
            self.model = model
            self.client = create_client(base_url=base_url, api_key=api_key)

    async def shutdown(self):
        client_to_close = None
        
        with self._lock:
            shutdown_event = self._shutdown_event
            # If shutdown is already in progress, wait for it
            if shutdown_event is not None and not shutdown_event.is_set():
                # Already shutting down, wait outside the lock
                pass
            else:
                # Start a new shutdown
                shutdown_event = asyncio.Event()
                self._shutdown_event = shutdown_event
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
