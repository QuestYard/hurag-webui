import asyncio

class LifespanClient:
    def __init__(self) -> None:
        self._lock = asyncio.Lock()
        self._shutdown_in_progress = False
        self._shutdown_complete_event = None
        self.model = None
        self.client = None

    @property
    def started(self) -> bool:
        # Note: This property is not lock-protected and may have race conditions
        # if checked during startup/shutdown. For accurate state, hold the lock.
        return self.client is not None

    async def startup(self, base_url, api_key, model):
        from hurag.llm import create_client
        async with self._lock:
            # Check if shutdown is in progress
            if self._shutdown_in_progress:
                raise RuntimeError("Cannot start client while shutdown is in progress")
            # Proceed with startup
            self.model = model
            self.client = create_client(base_url=base_url, api_key=api_key)

    async def shutdown(self):
        client_to_close = None
        shutdown_event = None
        should_perform_shutdown = False
        
        async with self._lock:
            # If shutdown already in progress, get the event to wait on
            if self._shutdown_in_progress:
                shutdown_event = self._shutdown_complete_event
            elif self.client is not None:
                # Start shutdown
                should_perform_shutdown = True
                self._shutdown_in_progress = True
                shutdown_event = asyncio.Event()
                self._shutdown_complete_event = shutdown_event
                self.model = None
                client_to_close = self.client
                self.client = None
            else:
                # No client to shutdown
                return
        
        # Wait for ongoing shutdown outside the lock
        if not should_perform_shutdown:
            await shutdown_event.wait()
            return
        
        # Perform the actual shutdown outside the lock
        try:
            await client_to_close.close()
        finally:
            # Mark shutdown as complete
            shutdown_event.set()
            async with self._lock:
                self._shutdown_in_progress = False
                self._shutdown_complete_event = None

# Global lifespan chat completions client
chat_client = LifespanClient()
