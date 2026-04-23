package in.ai.chatbot.config.config;

import org.springframework.ai.transformers.TransformersEmbeddingModel;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;

@Configuration
public class EmbeddingConfig {

    @Bean
    @Primary
    public TransformersEmbeddingModel embeddingModel() {
        return new TransformersEmbeddingModel();
    }
}
