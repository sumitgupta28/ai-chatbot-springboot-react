package in.ai.chatbot.config.controller;

import in.ai.chatbot.config.model.DocumentInfo;
import in.ai.chatbot.config.service.IngestionService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.util.List;

@Slf4j
@RestController
@RequestMapping("/documents")
public class DocumentController {

    private final IngestionService ingestionService;

    public DocumentController(IngestionService ingestionService) {
        this.ingestionService = ingestionService;
    }

    @PostMapping("/upload")
    public ResponseEntity<DocumentInfo> upload(@RequestParam("file") MultipartFile file) {
        log.debug("Upload request: {}", file.getOriginalFilename());
        try {
            return ResponseEntity.ok(ingestionService.ingest(file));
        } catch (Exception e) {
            log.error("Upload failed for {}: {}", file.getOriginalFilename(), e.getMessage(), e);
            return ResponseEntity.internalServerError().build();
        }
    }

    @GetMapping
    public List<DocumentInfo> list() {
        return ingestionService.listDocuments();
    }

    @DeleteMapping("/{id}")
    public ResponseEntity<Void> delete(@PathVariable Long id) {
        ingestionService.deleteDocument(id);
        return ResponseEntity.noContent().build();
    }
}
