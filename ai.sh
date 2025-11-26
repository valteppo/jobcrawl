#!/usr/bin/env bash

# Ensure server is running
ollama serve > /dev/null 2>&1 &
sleep 1

PROMPT="Summarize the movie Inception in one sentence."

json=$(cat <<EOF
{
  "model": "deepseek-r1:14b",
  "messages": [
    { "role": "user", "content": "$PROMPT" }
  ]
}
EOF
)

echo "Querying DeepSeek 14B..."
curl -s http://localhost:11434/api/chat \
  -d "$json" | jq -r '.message.content'