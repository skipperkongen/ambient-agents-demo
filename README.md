# ambient-agents-demo

This repository demonstrates a distributed ambient agent setup using
[MCP](https://github.com/crewai/mcp), [LangChain](https://python.langchain.com/),
[LangGraph](https://github.com/langchain-ai/langgraph),
[LangSmith](https://github.com/langchain-ai/langsmith) and Kafka. Agents run in
separate Docker containers and communicate over the network to handle customer
service emails about food deliveries.

## Components

- **Kafka** – single-node broker (KRaft mode) used for passing emails between
  agents.
- **Email Producer** – generates synthetic customer complaints using an LLM and
  publishes them to the `incoming-emails` topic.
- **Responder Agent** – HTTP service that uses an LLM to craft empathetic
  replies. Exposes a `/respond` endpoint and acts as a tool accessible via MCP.
- **Supervisor Agent** – consumes emails from Kafka, calls the responder via MCP
  using LangGraph, and publishes the final answer to the `outgoing-emails`
  topic.

The services are orchestrated with `docker-compose`. Start the demo with:

```bash
docker-compose up --build
```

Kafka will be exposed on `localhost:9092`. The supervisor logs show generated
emails and their replies.
