package in.ai.chatbot.config.tools;

import in.ai.chatbot.config.config.WeatherProperties;
import in.ai.chatbot.config.model.VisualCrossingResponse;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Component;
import org.springframework.web.client.RestClient;
import org.springframework.web.client.RestClientException;

@Slf4j
@Component
public class WeatherTool {

    private static final String BASE_URL =
            "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline";

    private final WeatherProperties weatherProperties;
    private final RestClient restClient;

    public WeatherTool(WeatherProperties weatherProperties) {
        this.weatherProperties = weatherProperties;
        this.restClient = RestClient.builder().baseUrl(BASE_URL).build();
    }

    @Tool(description = "Return the current weather for a given city. Use this when the user asks about the weather in a specific city.")
    public String getWeather(
            @ToolParam(description = "The name of the city, e.g. London, Tokyo, New York") String city) {
        log.debug("[tool:getWeather] city={}", city);

        if (weatherProperties.getApiKey() == null || weatherProperties.getApiKey().isBlank()) {
            log.warn("[tool:getWeather] VISUAL_CROSSING_API_KEY is not configured");
            return "Weather data is unavailable: the weather API key is not configured. "
                    + "Please set the VISUAL_CROSSING_API_KEY environment variable.";
        }

        try {
            VisualCrossingResponse response = restClient.get()
                    .uri("/{location}?unitGroup=metric&key={key}&contentType=json&include=current",
                            city, weatherProperties.getApiKey())
                    .retrieve()
                    .body(VisualCrossingResponse.class);

            if (response == null || response.currentConditions() == null) {
                log.warn("[tool:getWeather] empty response for city={}", city);
                return "Weather data not available for " + city + ".";
            }

            var cc = response.currentConditions();
            log.debug("[tool:getWeather] resolved={}, temp={}, conditions={}",
                    response.resolvedAddress(), cc.temp(), cc.conditions());

            return String.format("%s: %s, %.0f°C, humidity %.0f%%, wind %.0f km/h %s",
                    response.resolvedAddress(), cc.conditions(),
                    cc.temp(), cc.humidity(), cc.windspeed(), toCardinal(cc.winddir()));

        } catch (RestClientException e) {
            log.error("[tool:getWeather] HTTP error for city={}: {}", city, e.getMessage());
            return "Weather data not available for " + city + ". Please try again later.";
        } catch (Exception e) {
            log.error("[tool:getWeather] Unexpected error for city={}: {}", city, e.getMessage(), e);
            return "Weather data not available for " + city + ". Please try again later.";
        }
    }

    private static String toCardinal(double degrees) {
        String[] dirs = {"N", "NE", "E", "SE", "S", "SW", "W", "NW"};
        return dirs[(int) Math.round(degrees / 45.0) % 8];
    }
}
