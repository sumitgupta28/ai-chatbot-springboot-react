import logging

from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from langchain_core.messages import HumanMessage, SystemMessage

from app.dependencies import create_llm, get_vector_store
from app.services.rag_service import build_rag_context

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/rag/ai/chat/string/client")
async def rag_chat_client(
    message: str,
    topK: int = 5,
    similarityThreshold: float = 0.0,
    mode: str = "soft",
    temperature: float = 0.7,
    maxTokens: int = 1000,
    vector_store=Depends(get_vector_store),
):
    preview = message[:80].replace("\n", " ")
    logger.info(
        "RAG chat request: mode=%s topK=%d threshold=%s temperature=%s maxTokens=%d message='%s%s'",
        mode, topK, similarityThreshold, temperature, maxTokens,
        preview, "..." if len(message) > 80 else "",
    )

    ctx = await build_rag_context(message, vector_store, topK, similarityThreshold, mode)
    llm = create_llm(temperature=temperature, max_tokens=maxTokens)

    async def generate():
        if ctx.short_circuit:
            logger.info("RAG response: short-circuit (no matching documents)")
            yield f"data: {ctx.short_circuit_message}\n\n"
            yield "data: [DONE]\n\n"
            return

        messages = []
        if ctx.system_prompt:
            messages.append(SystemMessage(content=ctx.system_prompt))
            logger.debug("RAG system prompt injected (%d chars)", len(ctx.system_prompt))
        else:
            logger.debug("RAG: no system prompt (soft mode fallback to general knowledge)")
        messages.append(HumanMessage(content=message))

        token_count = 0
        try:
            async for chunk in llm.astream(messages):
                token = chunk.content
                if token:
                    token_count += 1
                    yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
            logger.debug("RAG stream complete: %d tokens emitted", token_count)
        except Exception:
            logger.error("Error during RAG stream for message='%s...'", preview, exc_info=True)
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
