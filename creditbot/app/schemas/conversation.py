from pydantic import BaseModel, Field


class SimulateMessageRequest(BaseModel):
    phone: str = Field(..., examples=["593999999999"])
    message: str = Field(..., examples=["Hola"])


class SimulateMessageResponse(BaseModel):
    phone: str
    reply: str
