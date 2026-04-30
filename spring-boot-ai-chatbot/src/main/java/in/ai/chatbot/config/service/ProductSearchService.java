package in.ai.chatbot.config.service;

import in.ai.chatbot.config.model.ProductInfo;
import in.ai.chatbot.config.repository.ProductRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.Objects;

@Slf4j
@Service
public class ProductSearchService {

    private final VectorStore productVectorStore;
    private final ProductRepository productRepository;
    private final ProductIngestionService productIngestionService;

    public ProductSearchService(@Qualifier("productVectorStore") VectorStore productVectorStore,
                                ProductRepository productRepository,
                                ProductIngestionService productIngestionService) {
        this.productVectorStore = productVectorStore;
        this.productRepository = productRepository;
        this.productIngestionService = productIngestionService;
    }

    public List<ProductInfo> search(String query, int topK, double similarityThreshold) {
        log.debug("Product semantic search: '{}' topK={} threshold={}", query, topK, similarityThreshold);

        List<Document> hits = productVectorStore.similaritySearch(
                SearchRequest.builder()
                        .query(query)
                        .topK(topK)
                        .similarityThreshold(similarityThreshold)
                        .build()
        );

        log.debug("Vector search returned {} hits", hits.size());

        return hits.stream()
                .map(doc -> {
                    Object pid = doc.getMetadata().get("product_id");
                    if (pid == null) return null;
                    return productRepository.findByProductId(pid.toString())
                            .map(productIngestionService::toDto)
                            .orElse(null);
                })
                .filter(Objects::nonNull)
                .toList();
    }
}
