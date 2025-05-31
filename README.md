# ambient-agents-demo
A demo of creating distributed ambient agents using different coding agents.

Inspirations:
- https://blog.langchain.dev/introducing-ambient-agents/

## Attempt 1

Prompt 1:

```

Implement an AI-powered customer service for a food delivery company. Customers write messages to the company and the company responds to and acts on those messages using a combination of AI agents and human agents.
Examples:
> Customer: I just received my food but it was the wrong order. I ordered burgers, not hot dogs. Please send me the right order or give me my money back.
> AI: Sorry about that, we will send you a delicious burger right away.
> Customer: The food was cold when I received it. I want my money back.
> AI agent: Sorry about that, I have handled your case over to my human colleague who will review your case, since it involves a request for monetary compensation.
> Human agent: I have reviewed your case and approved your request to get your money back.

Using docker-compose, create a small demo that runs Kafka in KRaft mode with two topics called `incoming-messages` and `outgoing-messages`.
Create two dummy workers written in Python:
Worker 1) generate and publish dummy events to `incoming-messages`, once per second. The event should have fields typical of an email.
Worker 2) consume events from `incoming-messages`, genererate a dummy response event and publish to `outgoing-messages`. Again, the event should have fields typical of an email.
Add info to README.md about how to run the demo.
```

## Concerns

- Tone of voice: a customer service department should always be polite.
- Risk: taking risky actions automatically, such as monetary compensation, should be guard railed, e.g., by requiring a human in the loop.

## Previous attempts

I tried using these prompts with Google Jules and OpenAI Codex. Not super successful. Too much at the same time, too many bugs.

### Prompt 1

Here I tried to one-shot the prompt to create the demo all at once. It failed.

```
Create an ambient agent demo using MCP, langchain, langgraph, langsmith, Kafka and docker-compose where agents running in different docker containers collaborate to handle customer service emails.
Create a fake email producer that uses an LLM to write synthetic customer service emails and publish them to kafka topic 'incoming-emails'.
Have a supervisor agent subscribe to these events and connect with tools and other agents over MCP and produce responses to the emails on kafka topic outgoing-emails''.
The example domain is food deliveries, where customers complain about their deliveries in different ways.
The multi agents should only communicate over the network using MCP where appropriate.
```


## Running the demo

The demo uses `docker-compose` to start a single Kafka broker in KRaft mode and two Python workers. One worker continuously produces dummy customer emails to the `incoming-messages` topic. The second worker consumes those messages and writes a simple reply to the `outgoing-messages` topic.

### Prerequisites

- Docker and docker-compose installed

### Steps

1. Start the environment:

   ```bash
   docker-compose up
   ```

   This will pull the required images, start Kafka, create the two topics and run both workers.

2. You should see the producer outputting messages once per second and the consumer printing the generated responses.

3. Stop the demo with `Ctrl+C` and remove the containers with:

   ```bash
   docker-compose down
   ```



