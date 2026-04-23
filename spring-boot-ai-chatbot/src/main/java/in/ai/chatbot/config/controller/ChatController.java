package in.ai.chatbot.config.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.ai.chat.messages.UserMessage;
import org.springframework.ai.chat.model.ChatModel;
import org.springframework.ai.chat.model.ChatResponse;
import org.springframework.ai.chat.prompt.Prompt;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;
import reactor.core.publisher.Flux;

@RestController
public class ChatController {

    private static final Logger log = LoggerFactory.getLogger(ChatController.class);

    private final ChatModel chatModel;

    @Autowired
    public ChatController(ChatModel chatModel) {
        this.chatModel = chatModel;
        log.debug("ChatController initialized with model: {}", chatModel.getClass().getSimpleName());
    }

    @GetMapping("/ai/chat")
    public Flux<ChatResponse> generateStream(@RequestParam(value = "message", defaultValue = "Tell me a joke") String message) {
        log.debug("[/ai/chat] Incoming message: '{}'", message);
        Prompt prompt = new Prompt(new UserMessage(message));
        log.debug("[/ai/chat] Dispatching prompt to model");
        return chatModel.stream(prompt)
                .doOnNext(cr -> {
                    String text = cr.getResult().getOutput().getText();
                    log.debug("[/ai/chat] Chunk received: '{}'", text);
                })
                .doOnComplete(() -> log.debug("[/ai/chat] Stream completed"))
                .doOnError(e -> log.debug("[/ai/chat] Stream error: {}", e.getMessage()));
    }

    @GetMapping("/ai/chat/string")
    public Flux<String> generateString(@RequestParam(value = "message", defaultValue = "Tell me a joke") String message) {
        log.debug("[/ai/chat/string] Incoming message: '{}'", message);
        Prompt prompt = new Prompt(new UserMessage(message));
        log.debug("[/ai/chat/string] Dispatching prompt to model");
        return chatModel.stream(prompt)
                .doOnNext(cr -> log.debug("[/ai/chat/string] Raw chunk from model: '{}'", cr.getResult().getOutput().getText()))
                .map(cr -> {
                    String text = cr.getResult().getOutput().getText();
                    return text != null ? text : "";
                })
                .filter(text -> !text.isEmpty())
                .doOnNext(text -> log.debug("[/ai/chat/string] Emitting token: '{}'", text))
                .doOnComplete(() -> log.debug("[/ai/chat/string] Stream completed"))
                .doOnError(e -> log.debug("[/ai/chat/string] Stream error: {}", e.getMessage()));
    }
}
