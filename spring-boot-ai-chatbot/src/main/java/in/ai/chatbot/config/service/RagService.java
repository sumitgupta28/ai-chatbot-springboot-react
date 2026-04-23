package in.ai.chatbot.config.service;

import in.ai.chatbot.config.config.RagProperties;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.document.Document;
import org.springframework.ai.vectorstore.SearchRequest;
import org.springframework.ai.vectorstore.VectorStore;
import org.springframework.stereotype.Service;

import java.util.List;
import java.util.stream.Collectors;

@Slf4j
@Service
public class RagService {

    private static final String SOFT_PROMPT = """
            You are a helpful assistant.

            Relevant context from uploaded documents:
            {context}

            Use the context above when it is relevant. Otherwise answer from your general knowledge.
            """;

    private static final String STRICT_PROMPT = """
            You are a helpful assistant that answers strictly from the provided document context.

            Relevant context from uploaded documents:
            {context}

            Answer ONLY based on the context above. If it does not contain enough information, reply: \
            "I don't have information about this in the uploaded documents."
            """;

    private final VectorStore vectorStore;
    private final RagProperties props;

    public RagService(VectorStore vectorStore, RagProperties props) {
        this.vectorStore = vectorStore;
        this.props = props;
    }

    public RagContext buildRagContext(String userMessage) {
        List<Document> hits = vectorStore.similaritySearch(
                SearchRequest.builder()
                        .query(userMessage)
                        .topK(props.getTopK())
                        .similarityThreshold(props.getSimilarityThreshold())
                        .build()
        );
        log.debug("RAG [{}] {} chunk(s) found for: '{}'", props.getMode(), hits.size(), userMessage);

        boolean strict = "strict".equalsIgnoreCase(props.getMode());

        if (hits.isEmpty()) {
            return strict
                    ? RagContext.shortCircuit("I don't have information about this in the uploaded documents.")
                    : RagContext.noSystemPrompt();
        }

        String context = hits.stream()
                .map(Document::getText)
                .collect(Collectors.joining("\n\n---\n\n"));

        String prompt = (strict ? STRICT_PROMPT : SOFT_PROMPT).replace("{context}", context);
        return RagContext.withPrompt(prompt);
    }

    public record RagContext(String systemPrompt, boolean shortCircuit, String shortCircuitMessage) {
        static RagContext withPrompt(String systemPrompt) {
            return new RagContext(systemPrompt, false, null);
        }
        static RagContext noSystemPrompt() {
            return new RagContext(null, false, null);
        }
        static RagContext shortCircuit(String message) {
            return new RagContext(null, true, message);
        }
    }
}
