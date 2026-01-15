from pydantic import BaseModel, Field
from typing import Self


class User(BaseModel):
    id: str | None = Field(default=None)
    account: str | None = Field(default="Guest", compare=False)
    username: str | None = Field(default="访客", compare=False)
    user_path: str | None = Field(default="访客", compare=False)

    def from_db_response(self, resp: tuple) -> Self:
        self.id = resp[0]
        self.account = resp[1]
        self.username = resp[2]
        self.user_path = resp[3]
        return self
