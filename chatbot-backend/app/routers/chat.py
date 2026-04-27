import logging

from fastapi import APIRouter
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage

from app.dependencies import get_llm

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/ai/chat/string")
async def chat_string(message: str = "Tell me a joke"):
    preview = message[:80].replace("\n", " ")
    logger.info("Chat request: message='%s%s'", preview, "..." if len(message) > 80 else "")
    llm = get_llm()

    async def generate():
        token_count = 0
        try:
            async for chunk in llm.astream([HumanMessage(content=message)]):
                token = chunk.content
                if token:
                    token_count += 1
                    yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
            logger.debug("Chat stream complete: %d tokens emitted", token_count)
        except Exception:
            logger.error("Error during chat stream for message='%s...'", preview, exc_info=True)
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
