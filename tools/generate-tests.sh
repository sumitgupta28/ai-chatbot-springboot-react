#!/usr/bin/env bash
# Usage: ./tools/generate-tests.sh <path-to-SourceFile.java>
# Generates a JUnit 5 + Mockito test skeleton alongside the source file.
#
# Prerequisites: claude CLI installed and authenticated (claude --version)

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <path-to-SourceFile.java>"
  exit 1
fi

SOURCE="$1"

if [[ ! -f "$SOURCE" ]]; then
  echo "Error: file not found: $SOURCE"
  exit 1
fi

if [[ "$SOURCE" != *.java ]]; then
  echo "Error: expected a .java file"
  exit 1
fi

OUTPUT="${SOURCE%.java}Test.java"

if [[ -f "$OUTPUT" ]]; then
  echo "Warning: $OUTPUT already exists — overwriting."
fi

echo "Reading $SOURCE ..."
SOURCE_CONTENT=$(cat "$SOURCE")

echo "Calling Claude to generate tests ..."
claude --print "You are a Java test engineer working on a Spring Boot 3.5 + Spring AI project.
Read the source file below and generate a complete JUnit 5 test class.

Rules:
- Use @ExtendWith(MockitoExtension.class) — NOT @SpringBootTest unless the class is a controller
- Mock every injected dependency with @Mock and @InjectMocks
- Cover: happy path for each public method, null/empty inputs, and one exception path per method
- Name test methods: should_<expectedResult>_when_<condition>
- Import only what is used — no wildcard imports
- Do NOT include any explanatory comments or docstrings, only code
- Match the exact package declaration of the source file
- Output ONLY the Java source — no markdown, no code fences, no explanation

Source file (${SOURCE}):
${SOURCE_CONTENT}" > "$OUTPUT"

echo "Generated: $OUTPUT"
