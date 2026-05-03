#!/usr/bin/env python3
"""Called by .github/workflows/pr-reviewer.yml — reads PR diff from stdin or argv[1],
calls Claude, prints a markdown review to stdout."""

import sys
import os
import anthropic

def main():
    if len(sys.argv) > 1:
        diff = sys.argv[1]
    else:
        diff = sys.stdin.read()

    if not diff.strip():
        print("## Claude PR Review\n\nNo diff content found — skipping review.")
        return

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        print("## Claude PR Review\n\n⚠️ ANTHROPIC_API_KEY not set — review skipped.")
        sys.exit(1)

    client = anthropic.Anthropic(api_key=api_key)

    truncated_diff = diff[:8000]
    was_truncated = len(diff) > 8000

    prompt = f"""You are a senior engineer reviewing a pull request for a Spring Boot 3.5 + Spring AI 1.1.4 + React 18 AI chatbot application.

Review the diff below and respond with a structured markdown review.

Focus areas (in order of importance):
1. **Spring AI patterns** — correct use of ChatClient, advisors (MessageChatMemoryAdvisor), VectorStore, EmbeddingModel
2. **Security** — SQL injection, secrets in logs or responses, CORS misconfigurations, missing input validation at controller boundaries
3. **Error handling** — unhandled exceptions at system boundaries (controllers, external API calls), missing null checks on optional returns
4. **Breaking changes** — controller method signature changes, response shape changes, removed/renamed endpoints
5. **Test coverage** — new service logic or controller endpoints with no corresponding test
6. **Code quality** — overly complex logic, missing Lombok annotations, unnecessary Spring bean instantiation

Format your response exactly as:

## Summary
One paragraph describing what this PR does.

## Issues Found
List each issue as: `[SEVERITY] File:Line — description` where SEVERITY is 🔴 Critical, 🟠 Major, or 🟡 Minor.
If no issues: write "No issues found."

## Suggestions
Up to 3 non-blocking improvement ideas.

## Verdict
Either: ✅ **Approve** — looks good to merge.
Or: ⚠️ **Needs Changes** — address the critical/major issues above before merging.

{"_Note: diff was truncated to 8000 chars._" if was_truncated else ""}

```diff
{truncated_diff}
```"""

    message = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    print(message.content[0].text)


if __name__ == "__main__":
    main()
