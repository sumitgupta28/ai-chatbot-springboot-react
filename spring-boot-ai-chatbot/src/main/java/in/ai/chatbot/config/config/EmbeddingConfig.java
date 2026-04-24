package in.ai.chatbot.config.config;

import org.springframework.ai.embedding.EmbeddingModel;
import org.springframework.ai.transformers.TransformersEmbeddingModel;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

@Configuration
public class EmbeddingConfig {

    /**
     * Configure TransformersEmbeddingModel as the primary embedding model.
     * Uses all-MiniLM-L6-v2 ONNX model (384 dimensions) from HuggingFace.
     * This prevents OllamaEmbeddingModel from being auto-configured.
     */
    @Bean
    @Primary
    public EmbeddingModel embeddingModel() {
        return new TransformersEmbeddingModel();
    }
}
