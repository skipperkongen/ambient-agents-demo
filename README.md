# ambient-agents-demo
A demo of creating distributed ambient agents using different coding agents.

## Prompts

### Prompt 1

```
Create an ambient agent demo using MCP, langchain, langgraph, langsmith, Kafka and docker-compose where agents running in different docker containers collaborate to handle customer service emails.
Create a fake email producer that uses an LLM to write synthetic customer service emails and publish them to kafka topic 'incoming-emails'.
Have a supervisor agent subscribe to these events and connect with tools and other agents over MCP and produce responses to the emails on kafka topic outgoing-emails''.
The example domain is food deliveries, where customers complain about their deliveries in different ways.
The multi agents should only communicate over the network using MCP where appropriate.
```

## OpenAI Codex

> branch `main-codex`

Attempts:
- Used [prompt 1](#Prompt 1), but the code didn't work in too many places. Learned about KRaft mode in Kafka.


## Google Jules

> branch `main-jules`

Attempts:
- Used [prompt 1](#Prompt 1), but the task was too big, so Jules timed out.

