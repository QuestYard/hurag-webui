from pydantic import BaseModel, Field
from datetime import datetime
from typing import Self


class Message(BaseModel):
    id: str | None = Field(default=None)
    session_id: str | None = Field(default=None, compare=False)
    seq_no: int | None = Field(default=None, compare=False)
    role: str | None = Field(default=None, compare=False)
    content: str | None = Field(default=None, compare=False, repr=False)
    created_ts: datetime | None = Field(default=None, compare=False)
    likes: int = Field(default=0, compare=False)
    dislikes: int = Field(default=0, compare=False)
    pair_id: str | None = Field(default=None, compare=False)

    def from_db_response(self, resp: tuple) -> Self:
        self.id = resp[0]
        self.session_id = resp[1]
        self.seq_no = resp[2]
        self.role = resp[3]
        self.content = resp[4]
        self.created_ts = resp[5]
        self.likes = resp[6]
        self.dislikes = resp[7]
        self.pair_id = resp[8]
        return self


class Session(BaseModel):
    id: str | None = Field(default=None)
    title: str | None = Field(default=None, compare=False)
    created_ts: datetime | None = Field(default=None, compare=False)
    user_id: str | None = Field(default=None, compare=False)

    def from_db_response(self, resp: tuple) -> Self:
        self.id = resp[0]
        self.title = resp[1]
        self.created_ts = resp[2]
        self.user_id = resp[3]
        return self
