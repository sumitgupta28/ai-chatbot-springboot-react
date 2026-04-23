package in.ai.chatbot.config.service;

import in.ai.chatbot.config.model.DocumentInfo;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.document.Document;
import org.springframework.ai.reader.tika.TikaDocumentReader;
import org.springframework.ai.transformer.splitter.TokenTextSplitter;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.jdbc.core.JdbcTemplate;
import org.springframework.jdbc.support.GeneratedKeyHolder;
import org.springframework.jdbc.support.KeyHolder;
import org.springframework.stereotype.Service;
import org.springframework.web.multipart.MultipartFile;

import java.sql.PreparedStatement;
import java.sql.Statement;
import java.util.List;

@Slf4j
@Service
public class IngestionService {

    private final VectorStore vectorStore;
    private final JdbcTemplate jdbcTemplate;
    private final TokenTextSplitter splitter = new TokenTextSplitter();

    public IngestionService(VectorStore vectorStore, JdbcTemplate jdbcTemplate) {
        this.vectorStore = vectorStore;
        this.jdbcTemplate = jdbcTemplate;
    }

    public DocumentInfo ingest(MultipartFile file) throws Exception {
        final String filename = file.getOriginalFilename();
        log.debug("Ingesting '{}'", filename);

        ByteArrayResource resource = new ByteArrayResource(file.getBytes()) {
            @Override
            public String getFilename() { return filename; }
        };

        TikaDocumentReader reader = new TikaDocumentReader(resource);
        List<Document> docs = reader.get();
        docs.forEach(d -> d.getMetadata().put("filename", filename));

        List<Document> chunks = splitter.apply(docs);
        chunks.forEach(c -> c.getMetadata().put("filename", filename));

        vectorStore.add(chunks);
        log.debug("Stored {} chunks for '{}'", chunks.size(), filename);

        KeyHolder keyHolder = new GeneratedKeyHolder();
        jdbcTemplate.update(con -> {
            PreparedStatement ps = con.prepareStatement(
                    "INSERT INTO document_metadata (filename, content_type, file_size, chunk_count) VALUES (?, ?, ?, ?)",
                    Statement.RETURN_GENERATED_KEYS
            );
            ps.setString(1, filename);
            ps.setString(2, file.getContentType());
            ps.setLong(3, file.getSize());
            ps.setInt(4, chunks.size());
            return ps;
        }, keyHolder);

        long id = ((Number) keyHolder.getKeys().get("id")).longValue();
        return fetchById(id);
    }

    public List<DocumentInfo> listDocuments() {
        return jdbcTemplate.query(
                "SELECT * FROM document_metadata ORDER BY upload_time DESC",
                (rs, rowNum) -> new DocumentInfo(
                        rs.getLong("id"),
                        rs.getString("filename"),
                        rs.getString("content_type"),
                        rs.getLong("file_size"),
                        rs.getTimestamp("upload_time").toLocalDateTime(),
                        rs.getInt("chunk_count")
                )
        );
    }

    public void deleteDocument(Long id) {
        List<String> filenames = jdbcTemplate.queryForList(
                "SELECT filename FROM document_metadata WHERE id = ?", String.class, id
        );
        if (filenames.isEmpty()) return;
        jdbcTemplate.update(
                "DELETE FROM vector_store WHERE metadata->>'filename' = ?", filenames.get(0)
        );
        jdbcTemplate.update("DELETE FROM document_metadata WHERE id = ?", id);
        log.debug("Deleted document id={} ({})", id, filenames.get(0));
    }

    private DocumentInfo fetchById(long id) {
        return jdbcTemplate.queryForObject(
                "SELECT * FROM document_metadata WHERE id = ?",
                (rs, rowNum) -> new DocumentInfo(
                        rs.getLong("id"),
                        rs.getString("filename"),
                        rs.getString("content_type"),
                        rs.getLong("file_size"),
                        rs.getTimestamp("upload_time").toLocalDateTime(),
                        rs.getInt("chunk_count")
                ),
                id
        );
    }
}
