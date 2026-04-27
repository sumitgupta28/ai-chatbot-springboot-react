import logging
from typing import List

from fastapi import APIRouter, Depends, File, UploadFile
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.dependencies import get_sync_engine, get_vector_store
from app.models.schemas import DocumentInfo, SearchResponse, VerifyResponse
from app.services import ingestion_service, rag_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents")


@router.get("/verify", response_model=VerifyResponse)
async def verify_vector_store(sync_engine=Depends(get_sync_engine)):
    logger.info("GET /documents/verify")
    count, docs = await rag_service.verify_vector_store(sync_engine)
    status = "ok" if count >= 0 else "error"
    logger.info("Vector store health: status=%s chunks=%d", status, max(count, 0))
    return VerifyResponse(
        status=status,
        documentsCount=count if count >= 0 else 0,
        documents=docs,
    )


@router.get("/verify/search", response_model=SearchResponse)
async def verify_search(
    query: str,
    topK: int = 10,
    similarityThreshold: float = 0.0,
    vector_store=Depends(get_vector_store),
):
    logger.info("GET /documents/verify/search: query='%s...' topK=%d threshold=%s", query[:60], topK, similarityThreshold)
    results = await rag_service.search_documents(query, vector_store, topK, similarityThreshold)
    logger.info("Search returned %d results", len(results))
    return SearchResponse(query=query, hitsFound=len(results), results=results)


@router.post("/upload", response_model=DocumentInfo)
async def upload_document(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    vector_store=Depends(get_vector_store),
):
    logger.info(
        "POST /documents/upload: filename='%s' content_type=%s",
        file.filename, file.content_type,
    )
    content = await file.read()
    result = await ingestion_service.ingest_document(
        filename=file.filename,
        content=content,
        content_type=file.content_type or "",
        file_size=len(content),
        vector_store=vector_store,
        db=db,
    )
    logger.info("Upload complete: id=%d filename='%s' chunks=%d", result.id, result.filename, result.chunkCount)
    return result


@router.get("", response_model=List[DocumentInfo])
async def list_documents(db: AsyncSession = Depends(get_db)):
    logger.debug("GET /documents")
    docs = await ingestion_service.list_documents(db)
    logger.debug("Returning %d documents", len(docs))
    return docs


@router.delete("/{doc_id}", status_code=204)
async def delete_document(
    doc_id: int,
    db: AsyncSession = Depends(get_db),
    vector_store=Depends(get_vector_store),
    sync_engine=Depends(get_sync_engine),
):
    logger.info("DELETE /documents/%d", doc_id)
    await ingestion_service.delete_document(doc_id, vector_store, sync_engine, db)
    logger.info("DELETE /documents/%d complete", doc_id)
    return Response(status_code=204)
