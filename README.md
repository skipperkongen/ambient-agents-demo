# ambient-agents-demo
A demo of creating distributed ambient agents using different coding agents.

Inspirations:
- https://blog.langchain.dev/introducing-ambient-agents/

## Demo use case

A food delivery company is implementing an AI-powered customer service. Customers write messages to the company and the company responds to and acts on those messages using a combination of AI agents and human agents.

Example of exchange:

```
Customer 1: I just received my food but it was the wrong order. I ordered burgers, not hot dogs. Please send me the right order or give me my money back.
AI: Sorry about that, we will send you a delicious burger right away.

Customer 2: The food was cold when I received it. I want my money back.
AI agent: Sorry about that, I have handled your case over to my human colleague who will review your case, since it involves a request for monetary compensation.
Human agent: I have reviewed your case and approved your request to get your money back.
```

## Concerns

- Tone of voice
- Taking risky actions automatically, such as monetary compensation.


## Prompts

### Prompt 1

Here I tried to one-shot the prompt to create the demo all at once. It failed.

```
Create an ambient agent demo using MCP, langchain, langgraph, langsmith, Kafka and docker-compose where agents running in different docker containers collaborate to handle customer service emails.
Create a fake email producer that uses an LLM to write synthetic customer service emails and publish them to kafka topic 'incoming-emails'.
Have a supervisor agent subscribe to these events and connect with tools and other agents over MCP and produce responses to the emails on kafka topic outgoing-emails''.
The example domain is food deliveries, where customers complain about their deliveries in different ways.
The multi agents should only communicate over the network using MCP where appropriate.
```

### Prompt 2

Here I start a bit slower, without all the GenAI complexity.

```
Using docker-compose, create a small demo that runs Kafka in KRaft mode with two topics called `incoming-messages` and `outgoing-messages`.
Create two dummy workers written in Python:
Worker 1) generate and publish dummy events to `incoming-messages`, once per second. The event should have fields typical of an email.
Worker 2) consume events from `incoming-messages`, genererate a dummy response event and publish to `outgoing-messages`. Again, the event should have fields typical of an email.
Overwrite the README.md and add info on how to run the demo. 
```

## OpenAI Codex

> branch `main-codex`

Number of burn downs: 1

Attempts:
- Used [prompt 1](#prompt-1), but the code didn't work in too many places. Learned about KRaft mode in Kafka.


## Google Jules

> branch `main-jules`

Attempts:
- Used [prompt 1](#prompt-1), but the task was too big, so Jules timed out.

