#!/usr/bin/env bash
# Usage: ./tools/generate-react-tests.sh <path-to-Component.js>
# Generates a Jest + React Testing Library test file alongside the component.
#
# Prerequisites: claude CLI installed and authenticated (claude --version)

set -euo pipefail

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 <path-to-Component.js>"
  exit 1
fi

SOURCE="$1"

if [[ ! -f "$SOURCE" ]]; then
  echo "Error: file not found: $SOURCE"
  exit 1
fi

if [[ "$SOURCE" != *.js ]]; then
  echo "Error: expected a .js file"
  exit 1
fi

BASENAME=$(basename "$SOURCE" .js)
DIR=$(dirname "$SOURCE")
OUTPUT="$DIR/$BASENAME.test.js"

if [[ -f "$OUTPUT" ]]; then
  echo "Warning: $OUTPUT already exists — overwriting."
fi

echo "Reading $SOURCE ..."
SOURCE_CONTENT=$(cat "$SOURCE")

echo "Calling Claude to generate tests ..."
claude --print "You are a React test engineer working on a React 18 + Tailwind CSS project.
Read the component below and generate a Jest + React Testing Library test file.

Rules:
- Import render, screen, waitFor, fireEvent from @testing-library/react
- Import userEvent from @testing-library/user-event
- Mock axios at the module level with jest.mock('axios')
- Cover: renders without crash, correct initial state, user interactions (button clicks, input changes), loading state, error state if the component handles errors
- Use descriptive test names: 'renders X', 'shows loading when...', 'calls API on submit'
- Do NOT include explanatory comments, only code
- Output ONLY the JavaScript source — no markdown, no code fences, no explanation

Component file (${SOURCE}):
${SOURCE_CONTENT}" > "$OUTPUT"

echo "Generated: $OUTPUT"
