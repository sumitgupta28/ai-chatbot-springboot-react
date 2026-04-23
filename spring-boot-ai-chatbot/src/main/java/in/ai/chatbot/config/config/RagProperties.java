package in.ai.chatbot.config.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "app.rag")
public class RagProperties {

    private String mode = "soft";
    private int topK = 5;
    private double similarityThreshold = 0.7;

    public String getMode() { return mode; }
    public void setMode(String mode) { this.mode = mode; }

    public int getTopK() { return topK; }
    public void setTopK(int topK) { this.topK = topK; }

    public double getSimilarityThreshold() { return similarityThreshold; }
    public void setSimilarityThreshold(double similarityThreshold) {
        this.similarityThreshold = similarityThreshold;
    }
}
