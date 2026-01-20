import threading

class LifespanClient:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._shutting_down = False
        self.model = None
        self.client = None

    @property
    def started(self) -> bool:
        with self._lock:
            return self.client is not None

    def startup(self, base_url, api_key, model):
        from hurag.llm import create_client
        with self._lock:
            if self._shutting_down:
                raise RuntimeError("Cannot start client while shutdown is in progress")
            self.model = model
            self.client = create_client(base_url=base_url, api_key=api_key)

    async def shutdown(self):
        client_to_close = None
        with self._lock:
            if self._shutting_down:
                return  # Already shutting down
            self._shutting_down = True
            self.model = None
            client_to_close = self.client
            self.client = None
        try:
            if client_to_close:
                await client_to_close.close()
        finally:
            with self._lock:
                self._shutting_down = False

# Global lifespan chat completions client
chat_client = LifespanClient()
