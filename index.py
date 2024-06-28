import os
from dotenv import load_dotenv
from langfuse import Langfuse
import uuid
from anthropic import AnthropicBedrock
from typing import List, Dict, Union


load_dotenv()

client = AnthropicBedrock(
    aws_secret_key=os.getenv("AWS_SECRET_KEY"),
    aws_access_key=os.getenv("AWS_ACCESS_KEY"),
    aws_region="us-east-1"
)

langfuse = Langfuse(
    secret_key=os.getenv("LANGFUSE_SECRET_KEY"),
    public_key=os.getenv("LANGFUSE_PUBLIC_KEY"),
    host = "https://cloud.langfuse.com",
)

session_id = str(uuid.uuid4())

async def call_llm_haiku_via_messages(
    system: str,
    messages: List[Dict[str, str]],
    user: str,
    temperature: float = 0,
    model: str = "claude-3-haiku-20240307",
    meta: Dict = {}
) -> str:
    # print("i reached here1")
    trace = langfuse.trace(
        name=user,
        session_id=session_id,
        input=str(messages),
        user_id=meta.get("type", "no-type"),
        version=model
    )
    # print("i reached here2")

    max_tokens = 2048

    generation = trace.generation(
        name="chat-completion",
        model=model,
        model_parameters={
            "temperature": temperature,
            "maxTokens": max_tokens,
        },
        input=[{"role": "system", "content": system}] + messages
    )
    # print("i reached here3")
    

    result = client.messages.create(
        temperature=temperature,
        system=system,
        messages=messages,
        model=model,
        max_tokens=max_tokens
    )
    # print("i reached here4")

    print("result.content[0].text", result.content[0].text)

    metadata: Dict[str, str] = {}
    trace.update(
        output=str(result.content),
        metadata=metadata
    )

    generation.end(
        output=result,
        version=model
    )

    return result.content[0].text