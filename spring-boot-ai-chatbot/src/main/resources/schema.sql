CREATE TABLE IF NOT EXISTS document_metadata (
    id           BIGSERIAL PRIMARY KEY,
    filename     VARCHAR(255) NOT NULL,
    content_type VARCHAR(100),
    file_size    BIGINT,
    upload_time  TIMESTAMP NOT NULL DEFAULT NOW(),
    chunk_count  INTEGER   NOT NULL DEFAULT 0
);
