package in.ai.chatbot.config.service;

import in.ai.chatbot.config.model.DocumentInfo;
import in.ai.chatbot.config.model.DocumentMetadata;
import in.ai.chatbot.config.repository.DocumentMetadataRepository;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.document.Document;
import org.springframework.ai.reader.tika.TikaDocumentReader;
import org.springframework.ai.transformer.splitter.TokenTextSplitter;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.core.io.ByteArrayResource;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@Slf4j
@Service
public class IngestionService {

    private final VectorStore vectorStore;
    private final DocumentMetadataRepository repository;
    private final TokenTextSplitter splitter = new TokenTextSplitter();

    @PersistenceContext
    private EntityManager entityManager;

    public IngestionService(VectorStore vectorStore, DocumentMetadataRepository repository) {
        this.vectorStore = vectorStore;
        this.repository = repository;
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

        DocumentMetadata saved = repository.save(
                DocumentMetadata.builder()
                        .filename(filename)
                        .contentType(file.getContentType())
                        .fileSize(file.getSize())
                        .chunkCount(chunks.size())
                        .build()
        );
        return toDto(saved);
    }

    public List<DocumentInfo> listDocuments() {
        return repository.findAllByOrderByUploadTimeDesc()
                .stream()
                .map(this::toDto)
                .toList();
    }

    @Transactional
    public void deleteDocument(Long id) {
        repository.findById(id).ifPresent(doc -> {
            entityManager.createNativeQuery(
                    "DELETE FROM vector_store WHERE metadata->>'filename' = :filename"
            ).setParameter("filename", doc.getFilename()).executeUpdate();
            repository.deleteById(id);
            log.debug("Deleted document id={} ({})", id, doc.getFilename());
        });
    }

    private DocumentInfo toDto(DocumentMetadata m) {
        return new DocumentInfo(m.getId(), m.getFilename(), m.getContentType(),
                m.getFileSize(), m.getUploadTime(), m.getChunkCount());
    }
}
