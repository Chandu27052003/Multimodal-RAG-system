import logging

from fastapi import APIRouter, HTTPException, status

from .config import settings
from .generator import get_generator
from .models import GenerateRequest, GenerateResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/generate", tags=["Generation"])


@router.post("/", response_model=GenerateResponse)
async def generate(request: GenerateRequest):
    """
    Generate a context-grounded response using the LLM.

    Receives a query and retrieved context block, returns a
    natural language answer grounded in the provided context.
    """
    if not request.context.strip():
        raise HTTPException(
            status_code=400,
            detail="Context cannot be empty. Retrieve relevant documents first.",
        )

    try:
        generator = get_generator()
        result = generator.generate(
            query=request.query,
            context=request.context,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"LLM generation failed: {e}",
        )

    return GenerateResponse(
        query=request.query,
        answer=result["answer"],
        model=result["model"],
        usage=result["usage"],
    )
