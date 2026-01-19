class LifespanClient:
    model = None
    client = None

    @property
    def started(self) -> bool:
        return self.client is not None

    def startup(self, base_url, api_key, model):
        from hurag.llm import create_client
        self.model = model
        self.client = create_client(base_url=base_url, api_key=api_key)

    async def shutdown(self):
        self.model = None
        if self.client:
            await self.client.close()
        self.client = None

# Global lifespan chat completions client
chat_client = LifespanClient()
