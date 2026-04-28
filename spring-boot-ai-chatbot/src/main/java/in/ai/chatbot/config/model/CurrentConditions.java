package in.ai.chatbot.config.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public record CurrentConditions(
        double temp,
        double humidity,
        double windspeed,
        double winddir,
        String conditions
) {}
