package in.ai.chatbot.config.tools;

import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.tool.annotation.Tool;
import org.springframework.ai.tool.annotation.ToolParam;
import org.springframework.stereotype.Component;

import java.time.ZonedDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Map;

@Slf4j
@Component
public class BuiltInTools {

    // ─── Calculator ──────────────────────────────────────────────────────────

    @Tool(description = "Add two numbers and return their sum. Use this whenever the user asks you to add numbers.")
    public String add(
            @ToolParam(description = "The first number") double a,
            @ToolParam(description = "The second number") double b) {
        double result = a + b;
        log.debug("[tool:add] {} + {} = {}", a, b, result);
        return String.valueOf(result);
    }

    @Tool(description = "Subtract the second number from the first. Use this whenever the user asks you to subtract numbers.")
    public String subtract(
            @ToolParam(description = "The number to subtract from") double a,
            @ToolParam(description = "The number to subtract") double b) {
        double result = a - b;
        log.debug("[tool:subtract] {} - {} = {}", a, b, result);
        return String.valueOf(result);
    }

    @Tool(description = "Multiply two numbers. Use this whenever the user asks you to multiply numbers.")
    public String multiply(
            @ToolParam(description = "The first number") double a,
            @ToolParam(description = "The second number") double b) {
        double result = a * b;
        log.debug("[tool:multiply] {} * {} = {}", a, b, result);
        return String.valueOf(result);
    }

    @Tool(description = "Divide the first number by the second. Returns an error message if the divisor is zero.")
    public String divide(
            @ToolParam(description = "The dividend") double a,
            @ToolParam(description = "The divisor") double b) {
        if (b == 0) {
            log.debug("[tool:divide] division by zero attempted");
            return "Error: division by zero is undefined";
        }
        double result = a / b;
        log.debug("[tool:divide] {} / {} = {}", a, b, result);
        return String.valueOf(result);
    }

    // ─── Date & Time ─────────────────────────────────────────────────────────

    @Tool(description = "Return the current date and time with timezone. Use this whenever the user asks about the current time, date, or day of the week.")
    public String getCurrentDateTime() {
        String now = ZonedDateTime.now().format(DateTimeFormatter.ISO_OFFSET_DATE_TIME);
        log.debug("[tool:getCurrentDateTime] {}", now);
        return now;
    }

    // ─── Weather (mock) ──────────────────────────────────────────────────────

    @Tool(description = "Return the current weather for a given city. Use this when the user asks about the weather in a specific city.")
    public String getWeather(
            @ToolParam(description = "The name of the city, e.g. London, Tokyo, New York") String city) {
        log.debug("[tool:getWeather] city={}", city);

        Map<String, String> mockData = Map.of(
            "london",   "Overcast, 13°C, humidity 78%, wind 20 km/h SW",
            "tokyo",    "Partly cloudy, 22°C, humidity 60%, wind 10 km/h N",
            "new york", "Sunny, 18°C, humidity 45%, wind 15 km/h NE",
            "paris",    "Light rain, 10°C, humidity 85%, wind 25 km/h W",
            "sydney",   "Clear skies, 27°C, humidity 50%, wind 12 km/h SE",
            "mumbai",   "Hot and humid, 34°C, humidity 88%, wind 8 km/h SW",
            "toronto",  "Cold and cloudy, 4°C, humidity 70%, wind 30 km/h N"
        );

        String weather = mockData.get(city.toLowerCase().trim());
        if (weather == null) {
            return "Weather data not available for " + city
                    + ". Known cities: London, Tokyo, New York, Paris, Sydney, Mumbai, Toronto.";
        }
        return city + ": " + weather;
    }
}
