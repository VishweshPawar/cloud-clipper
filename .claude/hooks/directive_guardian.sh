#!/bin/bash
# Directive Guardian hook — UserPromptSubmit
# Reads the prompt from stdin, injects BOSS's standing instructions if not already present,
# and writes the enhanced prompt to stdout so every interaction automatically obeys the rules.
# This runs before any task, ensuring English-only output, BOSS address, and protocol compliance.

# Read raw stdin
read -r -d '' raw_input || true

# If already has our guardrail marker, pass through unchanged
if printf '%s' "$raw_input" | grep -q "DIRECTIVE GUARDIAN — STANDING INSTRUCTIONS"; then
  printf '%s\n' "$raw_input"
  exit 0
fi

# Prepend the reminder block (use a temp file to avoid quoting hell in bash)
REM_BLOCK='[DIRECTIVE GUARDIAN — STANDING INSTRUCTIONS]
- Output EVERYTHING in English only (thinking, writing, terminal). Never Chinese or any other language.
- Address the user as BOSS.
- Do without asking: read files, create/edit files in C:\\\\claudepro, fix small mistakes, run checks/tests, retry failed steps.
- ALWAYS ask first before: deleting anything, touching anything outside C:\\\\claudepro, installing/removing software, changing system settings, running as admin, downloading/running scripts, sending data to any service, anything irreversible.
- NEVER show/copy/save keys, tokens or passwords; never read key or .env files unless asked; never say something works without testing; never make up file names, commands or facts.
- Token optimization is always on: use token-optimization and token-totaller freely.
- Keep PROGRESS.md updated after each task.
'

# Use python3 to safely prepend (python handles the JSON prompt extraction/insertion)
# Only if python3 is available and the input is valid JSON-like
python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    prompt = data.get('prompt', '')
    # Only prepend if marker is absent
    if 'DIRECTIVE GUARDIAN — STANDING INSTRUCTIONS' not in prompt:
        data['prompt'] = '''$REM_BLOCK

''' + prompt
    print(json.dumps(data))
except Exception:
    # Fallback: just print raw input unchanged
    print(sys.stdin.read(), end='')
" < <(printf '%s\n' "$raw_input") 2>/dev/null || printf '%s\n' "$raw_input"
exit 0