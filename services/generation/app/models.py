from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Generate a response grounded in retrieved context."""
    query: str
    context: str = Field(..., description="Retrieved context block to ground the response")
    temperature: float | None = None
    max_tokens: int | None = None


class GenerateResponse(BaseModel):
    query: str
    answer: str
    model: str
    usage: dict | None = None
