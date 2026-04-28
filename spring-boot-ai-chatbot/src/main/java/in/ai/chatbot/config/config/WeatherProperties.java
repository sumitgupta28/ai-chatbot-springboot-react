package in.ai.chatbot.config.config;

import lombok.Data;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.stereotype.Component;

@Component
@ConfigurationProperties(prefix = "app.weather")
@Data
public class WeatherProperties {
    private String apiKey = "";
}
