package in.ai.chatbot.config.model;

import com.fasterxml.jackson.annotation.JsonIgnoreProperties;

@JsonIgnoreProperties(ignoreUnknown = true)
public record VisualCrossingResponse(
        String resolvedAddress,
        CurrentConditions currentConditions
) {}
