import logging
from datetime import datetime
from typing import List

import anyio
from fastapi import HTTPException
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from langchain_postgres import PGVector
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.models.db import DocumentMetadata
from app.models.schemas import DocumentInfo
from app.parsers.docx_parser import extract_text_from_docx
from app.parsers.pdf_parser import extract_text_from_pdf
from app.parsers.txt_parser import extract_text_from_txt

logger = logging.getLogger(__name__)

COLLECTION_NAME = "chatbot_documents"

ACCEPTED_MIME_TYPES = {
    "application/pdf",
    "text/plain",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/msword",
}

_splitter = RecursiveCharacterTextSplitter(
    chunk_size=512,
    chunk_overlap=100,
    separators=["\n\n", "\n", ".", ",", "!", "?", ":", ";", " ", ""],
)


def _to_dto(doc: DocumentMetadata) -> DocumentInfo:
    return DocumentInfo(
        id=doc.id,
        filename=doc.filename,
        contentType=doc.content_type,
        fileSize=doc.file_size,
        uploadTime=doc.upload_time,
        chunkCount=doc.chunk_count,
    )


def _parse_document(content: bytes, content_type: str, filename: str) -> str:
    logger.debug("Parsing document: filename=%s content_type=%s", filename, content_type)
    if content_type == "application/pdf":
        return extract_text_from_pdf(content)
    if content_type in (
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        "application/msword",
    ):
        return extract_text_from_docx(content)
    return extract_text_from_txt(content)


async def ingest_document(
    filename: str,
    content: bytes,
    content_type: str,
    file_size: int,
    vector_store: PGVector,
    db: AsyncSession,
) -> DocumentInfo:
    logger.info("Ingesting document: filename=%s content_type=%s size=%d bytes", filename, content_type, file_size)

    if not filename or not filename.strip():
        logger.warning("Rejected upload: filename is blank")
        raise HTTPException(status_code=400, detail="Filename must not be blank")

    if not content:
        logger.warning("Rejected upload '%s': file is empty", filename)
        raise HTTPException(status_code=400, detail="File is empty")

    max_bytes = settings.max_upload_size_mb * 1024 * 1024
    if file_size > max_bytes:
        logger.warning(
            "Rejected upload '%s': size %d bytes exceeds limit of %d MB",
            filename, file_size, settings.max_upload_size_mb,
        )
        raise HTTPException(
            status_code=400,
            detail=f"File exceeds maximum size of {settings.max_upload_size_mb} MB",
        )

    normalised_type = (content_type or "").split(";")[0].strip().lower()
    if normalised_type not in ACCEPTED_MIME_TYPES:
        logger.warning("Rejected upload '%s': unsupported content_type=%s", filename, content_type)
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {content_type}. Accepted: PDF, TXT, DOCX",
        )

    extracted_text = _parse_document(content, normalised_type, filename)
    if not extracted_text or not extracted_text.strip():
        logger.warning("Text extraction produced no content for '%s'", filename)
        raise HTTPException(status_code=400, detail="Could not extract text from the document")

    logger.debug("Extracted %d characters from '%s'", len(extracted_text), filename)

    raw_chunks = _splitter.create_documents(
        [extracted_text], metadatas=[{"filename": filename}]
    )
    chunks: list[Document] = [
        c for c in raw_chunks if len(c.page_content.strip()) >= 50
    ]

    logger.debug(
        "Chunking '%s': %d raw chunks → %d usable chunks (min 50 chars)",
        filename, len(raw_chunks), len(chunks),
    )

    if not chunks:
        logger.warning("Chunking produced no usable chunks for '%s'", filename)
        raise HTTPException(
            status_code=400, detail="Document produced no usable chunks after splitting"
        )

    logger.info("Storing %d chunks for '%s' in vector store...", len(chunks), filename)
    await anyio.to_thread.run_sync(lambda: vector_store.add_documents(chunks))
    logger.debug("Chunks stored in vector store for '%s'", filename)

    doc_meta = DocumentMetadata(
        filename=filename,
        content_type=content_type,
        file_size=file_size,
        upload_time=datetime.utcnow(),
        chunk_count=len(chunks),
    )
    db.add(doc_meta)
    await db.commit()
    await db.refresh(doc_meta)

    logger.info(
        "Document ingested: id=%d filename='%s' chunks=%d",
        doc_meta.id, filename, len(chunks),
    )
    return _to_dto(doc_meta)


async def list_documents(db: AsyncSession) -> List[DocumentInfo]:
    logger.debug("Listing all documents from document_metadata")
    result = await db.execute(
        select(DocumentMetadata).order_by(DocumentMetadata.upload_time.desc())
    )
    rows = result.scalars().all()
    logger.debug("Found %d documents", len(rows))
    return [_to_dto(row) for row in rows]


async def delete_document(
    doc_id: int,
    vector_store: PGVector,
    sync_engine,
    db: AsyncSession,
) -> None:
    logger.info("Deleting document id=%d", doc_id)

    result = await db.execute(
        select(DocumentMetadata).where(DocumentMetadata.id == doc_id)
    )
    doc = result.scalar_one_or_none()
    if doc is None:
        logger.warning("Delete failed: document id=%d not found", doc_id)
        raise HTTPException(status_code=404, detail="Document not found")

    filename = doc.filename
    logger.debug("Deleting vectors for filename='%s' from langchain_pg_embedding", filename)

    def _delete_vectors():
        with sync_engine.connect() as conn:
            result = conn.execute(
                text(
                    """
                    DELETE FROM langchain_pg_embedding
                    WHERE cmetadata->>'filename' = :filename
                    AND collection_id = (
                        SELECT uuid FROM langchain_pg_collection WHERE name = :cname
                    )
                    """
                ),
                {"filename": filename, "cname": COLLECTION_NAME},
            )
            conn.commit()
            return result.rowcount

    deleted_rows = await anyio.to_thread.run_sync(_delete_vectors)
    logger.debug("Deleted %d vector rows for '%s'", deleted_rows, filename)

    await db.delete(doc)
    await db.commit()
    logger.info("Document deleted: id=%d filename='%s' (%d vectors removed)", doc_id, filename, deleted_rows)
