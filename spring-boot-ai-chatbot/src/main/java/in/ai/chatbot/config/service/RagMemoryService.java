package in.ai.chatbot.config.service;

import in.ai.chatbot.config.service.RagService.RagContext;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.ai.chat.memory.MessageWindowChatMemory;
import org.springframework.stereotype.Service;

@Slf4j
@Service
@RequiredArgsConstructor
public class RagMemoryService {

    private final RagService ragService;
    private final MessageWindowChatMemory messageWindowChatMemory;

    public RagContext buildRagContext(String message, int topK, double similarityThreshold, String mode) {
        return ragService.buildRagContext(message, topK, similarityThreshold, mode);
    }

    public void clearConversation(String conversationId) {
        messageWindowChatMemory.clear(conversationId);
        log.info("Cleared conversation memory for id={}", conversationId);
    }
}
