import os
from dotenv import load_dotenv
from langfuse import Langfuse
import uuid
from typing import List, Dict, Union
from openai import OpenAI

load_dotenv()

client = OpenAI(api_key=os.getenv("DEEPSEEK_API_KEY"), base_url="https://api.deepseek.com")

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

    trace = langfuse.trace(
        name=user,
        session_id=session_id,
        input=str(messages),
        user_id=meta.get("type", "no-type"),
        version=model
    )


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

    result = client.chat.completions.create(
    model="deepseek-chat",
    messages=messages,
    stream=False
)

    print(result.choices[0].message.content)

    metadata: Dict[str, str] = {}
    trace.update(
        output=str(result.choices[0].message),
        metadata=metadata
    )

    generation.end(
        output=result,
        version=model
    )

    return result.choices[0].message.content