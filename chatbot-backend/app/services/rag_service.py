import logging
from dataclasses import dataclass
from typing import List, Optional, Tuple

import anyio
from langchain_postgres import PGVector
from sqlalchemy import text

from app.models.schemas import SearchResult, VectorStoreInfo

logger = logging.getLogger(__name__)

COLLECTION_NAME = "chatbot_documents"

SOFT_PROMPT = """You are a helpful assistant.

Relevant context from uploaded documents:
{context}

Instructions:
1. If the context contains relevant information, prioritize using it and cite the source when helpful.
2. If the context doesn't fully cover the query, supplement with your general knowledge.
3. Never contradict information in the provided documents."""

STRICT_PROMPT = """You are a helpful assistant that answers strictly from the provided document context.

Relevant context from uploaded documents:
{context}

Instructions:
1. Answer ONLY based on the context provided above.
2. If the context does not contain sufficient information, reply: "I don't have information about this in the uploaded documents."
3. Do not use general knowledge beyond what is explicitly in the documents."""


@dataclass
class RagContext:
    system_prompt: Optional[str]
    short_circuit: bool
    short_circuit_message: Optional[str]


async def build_rag_context(
    message: str,
    vector_store: PGVector,
    top_k: int = 5,
    similarity_threshold: float = 0.0,
    mode: str = "soft",
) -> RagContext:
    preview = message[:80].replace("\n", " ")
    logger.info(
        "Building RAG context: mode=%s top_k=%d threshold=%s message='%s%s'",
        mode, top_k, similarity_threshold, preview, "..." if len(message) > 80 else "",
    )

    raw_results: List[Tuple] = await anyio.to_thread.run_sync(
        lambda: vector_store.similarity_search_with_score(message, k=top_k)
    )

    # similarity_search_with_score returns (Document, distance) where distance is cosine distance.
    # Convert: similarity = 1.0 - distance. Keep only chunks above threshold.
    filtered = [
        (doc, round(1.0 - dist, 4))
        for doc, dist in raw_results
        if round(1.0 - dist, 4) >= similarity_threshold
    ]

    logger.debug(
        "Vector search: %d raw results → %d above threshold %.2f",
        len(raw_results), len(filtered), similarity_threshold,
    )

    if filtered:
        scores = [score for _, score in filtered]
        logger.debug(
            "Chunk similarities: min=%.4f max=%.4f avg=%.4f (files: %s)",
            min(scores), max(scores), sum(scores) / len(scores),
            ", ".join({doc.metadata.get("filename", "?") for doc, _ in filtered}),
        )

    if not filtered:
        if mode == "strict":
            logger.warning(
                "RAG short-circuit (strict mode): no chunks above threshold %.2f for message='%s...'",
                similarity_threshold, preview,
            )
            return RagContext(
                system_prompt=None,
                short_circuit=True,
                short_circuit_message="I don't have information about this in the uploaded documents.",
            )
        logger.debug("No chunks found — proceeding without document context (soft mode)")
        return RagContext(system_prompt=None, short_circuit=False, short_circuit_message=None)

    context_text = "\n\n---\n\n".join(doc.page_content for doc, _ in filtered)
    template = SOFT_PROMPT if mode == "soft" else STRICT_PROMPT
    system_prompt = template.format(context=context_text)

    logger.info(
        "RAG context built: %d chunks used, context_length=%d chars",
        len(filtered), len(context_text),
    )
    return RagContext(system_prompt=system_prompt, short_circuit=False, short_circuit_message=None)


async def verify_vector_store(sync_engine) -> Tuple[int, List[VectorStoreInfo]]:
    logger.info("Verifying vector store contents (collection=%s)", COLLECTION_NAME)

    def _query():
        with sync_engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    SELECT e.content, e.cmetadata
                    FROM langchain_pg_embedding e
                    JOIN langchain_pg_collection c ON e.collection_id = c.uuid
                    WHERE c.name = :name
                    """
                ),
                {"name": COLLECTION_NAME},
            )
            return result.fetchall()

    try:
        rows = await anyio.to_thread.run_sync(_query)
        logger.debug("Raw row count from vector store: %d", len(rows))

        seen = set()
        docs: List[VectorStoreInfo] = []
        for row in rows:
            content = row[0] or ""
            if content in seen:
                continue
            seen.add(content)
            metadata = row[1] or {}
            docs.append(
                VectorStoreInfo(
                    filename=metadata.get("filename", "unknown"),
                    contentLength=len(content),
                    contentPreview=content[:100],
                )
            )

        logger.info("Vector store verified: %d unique chunks indexed", len(docs))
        return len(docs), docs

    except Exception:
        logger.error("Vector store verification failed", exc_info=True)
        return -1, []


async def search_documents(
    query: str,
    vector_store: PGVector,
    top_k: int = 10,
    similarity_threshold: float = 0.0,
) -> List[SearchResult]:
    preview = query[:80].replace("\n", " ")
    logger.info(
        "Similarity search: top_k=%d threshold=%s query='%s%s'",
        top_k, similarity_threshold, preview, "..." if len(query) > 80 else "",
    )

    raw_results: List[Tuple] = await anyio.to_thread.run_sync(
        lambda: vector_store.similarity_search_with_score(query, k=top_k)
    )

    results = [
        SearchResult(
            filename=doc.metadata.get("filename", "unknown"),
            similarity=round(1.0 - dist, 4),
            contentPreview=doc.page_content[:200],
        )
        for doc, dist in raw_results
        if round(1.0 - dist, 4) >= similarity_threshold
    ]

    results = sorted(results, key=lambda r: r.similarity, reverse=True)

    logger.info(
        "Search complete: %d/%d results above threshold %.2f",
        len(results), len(raw_results), similarity_threshold,
    )
    if results:
        logger.debug(
            "Top result: filename='%s' similarity=%.4f",
            results[0].filename, results[0].similarity,
        )

    return results
