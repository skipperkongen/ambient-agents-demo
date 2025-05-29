from fastapi import FastAPI
from pydantic import BaseModel
from langchain.llms import OpenAI

app = FastAPI()

class Email(BaseModel):
    email: str

@app.post("/respond")
def respond(email: Email):
    llm = OpenAI()
    prompt = (
        "You are a helpful customer service agent for a food delivery company."\
        " Craft a short empathetic reply to the following customer email:"\
        f"\n{email.email}"
    )
    response = llm(prompt)
    return {"response": response}
