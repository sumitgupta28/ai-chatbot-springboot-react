package in.ai.chatbot.config.controller;

import in.ai.chatbot.config.service.RagService;
import in.ai.chatbot.config.service.RagService.RagContext;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.chat.client.ChatClient;
import org.springframework.ai.chat.messages.SystemMessage;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.chat.model.ChatResponse;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

import java.util.List;

@Slf4j
@RestController
public class ChatController {

    private final ChatModel chatModel;
    private final RagService ragService;
    private final ChatClient chatClient;

    @Autowired
    public ChatController(ChatModel chatModel, RagService ragService, ChatClient chatClient) {
        this.chatModel = chatModel;
        this.ragService = ragService;
        this.chatClient = chatClient;
        log.debug("ChatController initialized with model: {}", chatModel.getClass().getSimpleName());
    }

    @GetMapping("/ai/chat")
    public Flux<ChatResponse> generateStream(
            @RequestParam(value = "message") String message) {
        log.debug("[/ai/chat] message: '{}'", message);
        RagContext ctx = ragService.buildRagContext(message);
        if (ctx.shortCircuit()) {
            return chatModel.stream(new Prompt(new UserMessage(ctx.shortCircuitMessage())));
        }
        return chatModel.stream(buildPrompt(message, ctx.systemPrompt()))
                .doOnComplete(() -> log.debug("[/ai/chat] stream completed"))
                .doOnError(e -> log.debug("[/ai/chat] stream error: {}", e.getMessage()));
    }

    @GetMapping("/ai/chat/string")
    public Flux<String> generateString(
            @RequestParam(value = "message") String message) {
        log.debug("[/ai/chat/string] message: '{}'", message);
        RagContext ctx = ragService.buildRagContext(message);
        if (ctx.shortCircuit()) {
            return Flux.just(ctx.shortCircuitMessage());
        }
        return chatModel.stream(buildPrompt(message, ctx.systemPrompt()))

                .map(cr -> {
                    String text = cr.getResult().getOutput().getText();
                    return text != null ? text : "";
                })
                .filter(text -> !text.isEmpty())
                .doOnComplete(() -> log.debug("[/ai/chat/string] stream completed"))
                .doOnError(e -> log.debug("[/ai/chat/string] stream error: {}", e.getMessage()));
    }

    @GetMapping("/ai/chat/string/client")
    public Flux<String> generateStringWithClient(
            @RequestParam(value = "message") String message) {
        log.debug("[/ai/chat/string/client] message: '{}'", message);
        RagContext ctx = ragService.buildRagContext(message);
        if (ctx.shortCircuit()) {
            return Flux.just(ctx.shortCircuitMessage());
        }
        var promptSpec = chatClient.prompt();
        if (ctx.systemPrompt() != null && !ctx.systemPrompt().isBlank()) {
            promptSpec = promptSpec.system(ctx.systemPrompt());
        }
        return promptSpec
                .user(message)
                .stream()
                .content()
                .doOnComplete(() -> log.debug("[/ai/chat/string/client] stream completed"))
                .doOnError(e -> log.debug("[/ai/chat/string/client] stream error: {}", e.getMessage()));
    }

    private Prompt buildPrompt(String userMessage, String systemPrompt) {
        if (systemPrompt != null && !systemPrompt.isBlank()) {
            return new Prompt(List.of(new SystemMessage(systemPrompt), new UserMessage(userMessage)));
        }
        return new Prompt(new UserMessage(userMessage));
    }
}
