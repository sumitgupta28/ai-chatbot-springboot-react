package in.ai.chatbot.config.repository;

import in.ai.chatbot.config.model.ConversationMessage;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Modifying;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;

import java.util.List;

@Repository
public interface ConversationMessageRepository extends JpaRepository<ConversationMessage, Long> {

    List<ConversationMessage> findByConversationIdOrderByMessageIndexAsc(String conversationId);

    @Modifying
    @Query("DELETE FROM ConversationMessage c WHERE c.conversationId = :conversationId")
    void deleteByConversationId(@Param("conversationId") String conversationId);

    @Query("SELECT DISTINCT c.conversationId FROM ConversationMessage c")
    List<String> findDistinctConversationIds();
}
