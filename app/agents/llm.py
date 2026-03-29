import openai
import json
from dotenv import load_dotenv
from openai.types.chat.chat_completion import ChatCompletionMessage
from app.core.config import settings

load_dotenv()

client = openai.OpenAI(
    api_key=settings.openai_api_key,
    base_url=settings.openai_url,
)


class LLMClient:
    def __init__(self, model: str = None):
        self.model = model or settings.openai_model_name

    def run(self, messages: list) -> ChatCompletionMessage:
        from app.agents.tools import TOOL_SCHEMAS

        print(f"[LLM] Sending {len(messages)} messages")
        for i, m in enumerate(messages):
            print(f"[LLM]   [{i}] role={m.get('role')}, keys={list(m.keys())}")

        resp = client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=TOOL_SCHEMAS,
            temperature=0.7,
        )
        message = resp.choices[0].message
        print(f"[LLM] Response: role={message.role}, tool_calls={bool(message.tool_calls)}")
        if message.tool_calls:
            for tc in message.tool_calls:
                print(f"[LLM]   tc id={tc.id}, fn={tc.function.name}")
        return message
